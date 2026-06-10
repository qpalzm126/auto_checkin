"""
Telegram 通知服務
透過 Telegram Bot 發送打卡通知
"""
import os
import requests
import datetime


class TelegramService:
    """Telegram 通知服務"""
    
    @staticmethod
    def get_config():
        """取得 Telegram 設定"""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        return token, chat_id
    
    @staticmethod
    def is_enabled() -> bool:
        """檢查 Telegram 通知是否已啟用"""
        token, chat_id = TelegramService.get_config()
        return bool(token and chat_id)
    
    @staticmethod
    def send_message(message: str, parse_mode: str = "HTML", return_message_id: bool = False):
        """
        發送訊息到 Telegram
        
        Args:
            message: 要發送的訊息內容
            parse_mode: 訊息格式（HTML 或 Markdown）
            return_message_id: 若為 True，成功時回傳 message_id (int)，失敗時回傳 None
            
        Returns:
            bool 或 int 或 None
        """
        token, chat_id = TelegramService.get_config()
        
        if not token or not chat_id:
            print("ℹ️ Telegram 未設定，跳過通知")
            print("💡 請設定環境變數: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
            return None if return_message_id else False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("📱 Telegram 通知發送成功")
                if return_message_id:
                    return response.json().get("result", {}).get("message_id")
                return True
            else:
                print(f"❌ Telegram 通知發送失敗: {response.status_code}")
                print(f"   回應: {response.text}")
                return None if return_message_id else False
        except Exception as e:
            print(f"❌ Telegram 通知發送失敗: {e}")
            return None if return_message_id else False
    
    @staticmethod
    def edit_message(message_id: int, message: str, parse_mode: str = "HTML") -> bool:
        """
        編輯已發送的訊息（用來更新進度）
        
        Args:
            message_id: 要編輯的訊息 ID
            message: 新的訊息內容
            parse_mode: 訊息格式
            
        Returns:
            bool: 是否編輯成功
        """
        token, chat_id = TelegramService.get_config()
        
        if not token or not chat_id or not message_id:
            return False
        
        url = f"https://api.telegram.org/bot{token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            # 訊息內容沒變動時 Telegram 會回 400，這個錯誤可以忽略
            if response.status_code == 400 and "not modified" in response.text.lower():
                return True
            print(f"⚠️ 編輯訊息失敗: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"⚠️ 編輯訊息失敗: {e}")
            return False
    
    @staticmethod
    def send_checkin_notification(
        result: str,
        label: str,
        source: str = None,
        check_in_time: str = None,
        check_out_time: str = None,
    ) -> bool:
        """
        發送打卡通知
        
        Args:
            result: 打卡結果
            label: 打卡標籤（上班、下班等）
            source: 打卡來源
            check_in_time: 上班時間
            check_out_time: 下班時間
        """
        # 判斷狀態圖示
        if "成功" in result or "完成" in result:
            icon = "✅"
            status_emoji = "🎉"
        elif "失敗" in result or "錯誤" in result:
            icon = "❌"
            status_emoji = "⚠️"
        elif "略過" in result or "不足" in result:
            icon = "⏸"
            status_emoji = "ℹ️"
        else:
            icon = "📝"
            status_emoji = "📋"
        
        # 取得當前時間
        now = datetime.datetime.now()
        
        # 組裝訊息
        message_parts = [
            f"{status_emoji} <b>打卡通知</b>",
            "",
            f"{icon} <b>動作:</b> {label}",
            f"📊 <b>結果:</b> {result}",
        ]
        
        if source:
            message_parts.append(f"🔧 <b>來源:</b> {source}")
        
        if check_in_time and check_in_time != "未抓取":
            message_parts.append(f"🕘 <b>上班時間:</b> {check_in_time}")
        
        if check_out_time and check_out_time != "未抓取":
            message_parts.append(f"🕔 <b>下班時間:</b> {check_out_time}")
        
        message_parts.append(f"⏰ <b>通知時間:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        message = "\n".join(message_parts)
        
        return TelegramService.send_message(message)
    
    @staticmethod
    def send_status_report(
        check_in_time: str = None,
        check_out_time: str = None,
        records: list = None,
        work_hours: float = None,
    ) -> bool:
        """
        發送打卡狀態報告
        
        Args:
            check_in_time: 上班時間
            check_out_time: 下班時間
            records: 打卡記錄列表
            work_hours: 已工作時數
        """
        now = datetime.datetime.now()
        message_parts = [
            "📊 <b>打卡狀態報告</b>",
            "",
            f"📅 <b>日期:</b> {now.strftime('%Y-%m-%d')}",
            f"⏰ <b>查詢時間:</b> {now.strftime('%H:%M:%S')}",
            "",
        ]
        
        if check_in_time:
            message_parts.append(f"🕘 <b>上班時間:</b> {check_in_time}")
        
        if check_out_time:
            message_parts.append(f"🕔 <b>下班時間:</b> {check_out_time}")
        
        if work_hours is not None:
            message_parts.append(f"⏱ <b>已工作:</b> {work_hours:.1f} 小時")
        
        if records:
            message_parts.append("")
            message_parts.append("📝 <b>今日打卡記錄:</b>")
            for i, record in enumerate(records, 1):
                check_in = record.get('check_in', '無')
                check_out = record.get('check_out', '無')
                message_parts.append(f"  {i}. {check_in} ~ {check_out}")
        
        message = "\n".join(message_parts)
        return TelegramService.send_message(message)
    
    @staticmethod
    def test_connection() -> bool:
        """測試 Telegram 連線"""
        if not TelegramService.is_enabled():
            print("❌ Telegram 未設定")
            print("💡 請在 .env 設定:")
            print("   TELEGRAM_BOT_TOKEN=你的_bot_token")
            print("   TELEGRAM_CHAT_ID=你的_chat_id")
            return False
        
        test_message = (
            "🤖 <b>Telegram Bot 測試</b>\n"
            "\n"
            f"✅ 連線成功！\n"
            f"⏰ 測試時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
            "👉 你的自動打卡系統已經設定完成，往後打卡狀態都會通知到這裡。"
        )
        
        return TelegramService.send_message(test_message)


if __name__ == "__main__":
    # 測試 Telegram 設定
    print("🔍 測試 Telegram 設定...")
    TelegramService.test_connection()
