"""
Telegram Bot 互動式監聽器
透過 Long Polling 接收使用者的指令並回應
支援任務追蹤、進度回報、取消機制
"""
import os
import time
import datetime
import threading
import requests
from telegram_service import TelegramService


class TaskCancelled(Exception):
    """任務被使用者取消"""
    pass


class ProgressReporter:
    """進度回報器 - 透過編輯同一則 Telegram 訊息來顯示階段"""
    
    def __init__(self, task_name: str, cancel_event: threading.Event):
        self.task_name = task_name
        self.cancel_event = cancel_event
        self.message_id = None
        self.steps = []
        self.start_time = time.time()
        self.last_update_time = 0
    
    def _build_message(self, status_emoji: str = "⏳") -> str:
        """組裝進度訊息"""
        elapsed = time.time() - self.start_time
        
        lines = [
            f"{status_emoji} <b>執行中: {self.task_name}</b>",
            f"⏱ 已用時: {elapsed:.1f} 秒",
            "",
            "<b>進度:</b>",
        ]
        
        for i, (step, status) in enumerate(self.steps, 1):
            lines.append(f"{status} {step}")
        
        return "\n".join(lines)
    
    def start(self, first_step: str):
        """開始任務（發送第一則訊息）"""
        self.steps.append((first_step, "🔄"))
        message = self._build_message()
        self.message_id = TelegramService.send_message(
            message, return_message_id=True
        )
        self.last_update_time = time.time()
    
    def step(self, name: str):
        """完成上一步並開始下一步"""
        # 檢查是否被取消
        self.check_cancelled()
        
        # 將上一步標記為完成
        if self.steps:
            last_name, _ = self.steps[-1]
            self.steps[-1] = (last_name, "✅")
        
        # 加入新步驟
        self.steps.append((name, "🔄"))
        self._update()
    
    def update(self, message: str = None):
        """強制更新訊息（節流：1 秒內最多一次）"""
        now = time.time()
        if now - self.last_update_time < 1.0:
            return
        self._update()
    
    def _update(self):
        """實際執行訊息編輯"""
        if not self.message_id:
            return
        try:
            TelegramService.edit_message(
                self.message_id, self._build_message()
            )
            self.last_update_time = time.time()
        except Exception as e:
            print(f"⚠️ 進度更新失敗: {e}")
    
    def complete(self, summary: str = ""):
        """標記任務完成"""
        if self.steps:
            last_name, _ = self.steps[-1]
            self.steps[-1] = (last_name, "✅")
        
        if not self.message_id:
            return
        
        elapsed = time.time() - self.start_time
        lines = [
            f"🎉 <b>完成: {self.task_name}</b>",
            f"⏱ 總用時: {elapsed:.1f} 秒",
        ]
        if summary:
            lines.append("")
            lines.append(summary)
        lines.append("")
        lines.append("<b>步驟:</b>")
        for step, status in self.steps:
            lines.append(f"{status} {step}")
        
        TelegramService.edit_message(self.message_id, "\n".join(lines))
    
    def fail(self, error: str):
        """標記任務失敗"""
        if self.steps:
            last_name, _ = self.steps[-1]
            self.steps[-1] = (last_name, "❌")
        
        if not self.message_id:
            return
        
        elapsed = time.time() - self.start_time
        lines = [
            f"❌ <b>失敗: {self.task_name}</b>",
            f"⏱ 用時: {elapsed:.1f} 秒",
            "",
            f"<b>錯誤:</b> {error}",
            "",
            "<b>步驟:</b>",
        ]
        for step, status in self.steps:
            lines.append(f"{status} {step}")
        
        TelegramService.edit_message(self.message_id, "\n".join(lines))
    
    def cancelled(self):
        """標記任務被取消"""
        if self.steps:
            last_name, _ = self.steps[-1]
            self.steps[-1] = (last_name, "🛑")
        
        if not self.message_id:
            return
        
        elapsed = time.time() - self.start_time
        lines = [
            f"🛑 <b>已取消: {self.task_name}</b>",
            f"⏱ 用時: {elapsed:.1f} 秒",
            "",
            "<b>步驟:</b>",
        ]
        for step, status in self.steps:
            lines.append(f"{status} {step}")
        
        TelegramService.edit_message(self.message_id, "\n".join(lines))
    
    def check_cancelled(self):
        """檢查是否被取消，若是則拋出例外"""
        if self.cancel_event.is_set():
            raise TaskCancelled("任務已被使用者取消")


class TelegramBotListener:
    """Telegram Bot 監聽器"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.last_update_id = 0
        self.running = False
        self.commands = {}
        self.thread = None
        
        # 任務追蹤
        self.current_task = None  # 當前任務名稱
        self.current_task_thread = None  # 當前任務的執行緒
        self.cancel_event = threading.Event()  # 取消信號
        self.task_lock = threading.Lock()
    
    def register_command(self, command: str, handler, cancellable: bool = True):
        """
        註冊指令處理器
        
        Args:
            command: 指令名稱（不含 /）
            handler: 處理函數，會收到 (args: str, reporter: ProgressReporter) 參數
                     如果 cancellable=False，handler 只會收到 (args: str)
            cancellable: 是否可以被取消
        """
        self.commands[command.lower()] = (handler, cancellable)
    
    def _send_message(self, message: str):
        """發送訊息"""
        TelegramService.send_message(message)
    
    def _get_updates(self, timeout: int = 30):
        """獲取新訊息（long polling）"""
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": timeout,
        }
        
        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            if response.status_code == 200:
                return response.json().get("result", [])
            else:
                print(f"⚠️ 獲取訊息失敗: {response.status_code}")
                return []
        except requests.exceptions.Timeout:
            return []
        except Exception as e:
            print(f"⚠️ 獲取訊息出錯: {e}")
            return []
    
    def _execute_task(self, command: str, handler, cancellable: bool, args: str):
        """在獨立執行緒中執行任務"""
        reporter = None
        try:
            if cancellable:
                # 建立 reporter 給 handler 用
                reporter = ProgressReporter(
                    task_name=f"/{command}",
                    cancel_event=self.cancel_event,
                )
                handler(args, reporter)
            else:
                handler(args)
        except TaskCancelled:
            print(f"🛑 任務 /{command} 被取消")
            if reporter:
                reporter.cancelled()
        except Exception as e:
            print(f"❌ 任務 /{command} 執行出錯: {e}")
            if reporter:
                reporter.fail(str(e))
            else:
                self._send_message(f"❌ <b>任務執行失敗</b>\n{e}")
        finally:
            with self.task_lock:
                self.current_task = None
                self.current_task_thread = None
                self.cancel_event.clear()
    
    def _process_update(self, update: dict):
        """處理單一更新"""
        self.last_update_id = update["update_id"]
        
        message = update.get("message")
        if not message:
            return
        
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        # 只處理授權的 chat_id
        if chat_id != self.chat_id:
            print(f"⚠️ 收到來自未授權 chat_id 的訊息: {chat_id}")
            return
        
        text = message.get("text", "").strip()
        if not text:
            return
        
        user_name = message.get("from", {}).get("first_name", "User")
        print(f"📩 收到訊息 from {user_name}: {text}")
        
        # 解析指令
        if text.startswith("/"):
            parts = text[1:].split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            # 移除 @bot_name 後綴（如果有的話）
            if "@" in command:
                command = command.split("@")[0]
            
            # 特殊指令: /cancel 和 /current
            if command in ("cancel", "stop"):
                self._handle_cancel()
                return
            
            if command in ("current", "now"):
                self._handle_current()
                return
            
            handler_info = self.commands.get(command)
            if not handler_info:
                self._send_message(
                    f"❓ 未知指令: /{command}\n\n"
                    f"可用指令:\n" + 
                    "\n".join([f"  /{cmd}" for cmd in self.commands.keys()]) +
                    f"\n  /current - 查看當前任務\n  /cancel - 取消當前任務"
                )
                return
            
            handler, cancellable = handler_info
            
            # 檢查是否有任務正在執行
            with self.task_lock:
                if self.current_task:
                    self._send_message(
                        f"⚠️ <b>已有任務在執行</b>\n"
                        f"當前任務: /{self.current_task}\n\n"
                        f"請先 /cancel 或等待當前任務完成"
                    )
                    return
                
                # 建立新任務
                self.current_task = command
                self.cancel_event.clear()
                self.current_task_thread = threading.Thread(
                    target=self._execute_task,
                    args=(command, handler, cancellable, args),
                    daemon=True,
                )
                self.current_task_thread.start()
                print(f"⚙️ 啟動任務: /{command}")
        else:
            # 非指令訊息
            self._send_message(
                "💡 請使用以下指令:\n" +
                "\n".join([f"  /{cmd}" for cmd in self.commands.keys()]) +
                "\n  /current - 查看當前任務\n  /cancel - 取消當前任務"
            )
    
    def _handle_cancel(self):
        """處理取消指令"""
        with self.task_lock:
            if not self.current_task:
                self._send_message("ℹ️ 目前沒有任務在執行")
                return
            
            task_name = self.current_task
            print(f"🛑 收到取消指令，正在取消: /{task_name}")
            self.cancel_event.set()
            self._send_message(
                f"🛑 <b>取消請求已發送</b>\n"
                f"任務: /{task_name}\n\n"
                f"任務將在下個檢查點停止..."
            )
    
    def _handle_current(self):
        """查詢當前任務"""
        with self.task_lock:
            if not self.current_task:
                self._send_message("ℹ️ 目前沒有任務在執行")
            else:
                self._send_message(
                    f"⚙️ <b>當前任務</b>\n"
                    f"指令: /{self.current_task}\n\n"
                    f"💡 使用 /cancel 取消任務"
                )
    
    def _polling_loop(self):
        """主要輪詢迴圈"""
        print("🤖 Telegram Bot 監聽器啟動中...")
        
        # 啟動通知
        startup_msg = (
            "🤖 <b>Bot 已啟動</b>\n"
            f"⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
            "可用指令:\n" +
            "\n".join([f"  /{cmd}" for cmd in self.commands.keys()]) +
            "\n  /current - 查看當前任務\n  /cancel - 取消當前任務"
        )
        self._send_message(startup_msg)
        
        # 先清掉舊訊息
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            response = requests.get(url, params={"offset": -1}, timeout=10)
            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    self.last_update_id = results[-1]["update_id"]
                    print(f"📌 略過 {len(results)} 筆舊訊息")
        except Exception:
            pass
        
        print("✅ Telegram Bot 已啟動，等待指令...")
        
        while self.running:
            try:
                updates = self._get_updates(timeout=30)
                for update in updates:
                    self._process_update(update)
            except Exception as e:
                print(f"⚠️ 監聽迴圈出錯: {e}")
                time.sleep(5)
    
    def start(self, blocking: bool = True):
        """
        啟動監聽器
        
        Args:
            blocking: True 為阻塞模式，False 為背景執行
        """
        if not self.token or not self.chat_id:
            print("❌ Telegram 設定不完整")
            return False
        
        if not self.commands:
            print("⚠️ 尚未註冊任何指令")
        
        self.running = True
        
        if blocking:
            try:
                self._polling_loop()
            except KeyboardInterrupt:
                print("\n👋 收到中斷信號，停止 Bot...")
                self.stop()
        else:
            self.thread = threading.Thread(target=self._polling_loop, daemon=True)
            self.thread.start()
        
        return True
    
    def stop(self):
        """停止監聽器"""
        self.running = False
        if self.current_task:
            self.cancel_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self._send_message("👋 <b>Bot 已停止</b>")
        print("✅ Telegram Bot 已停止")
