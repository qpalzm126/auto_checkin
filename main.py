"""
自動打卡系統主程式
重構版本 - 使用模組化設計
"""
import os
import sys
import time
import datetime
import schedule
from config import Config
from web_automation import WebAutomation
from email_service import EmailService
from vpn_service import VPNService
from telegram_service import TelegramService
from telegram_bot_listener import TelegramBotListener, TaskCancelled
import schedule_config


# ===== 排程時間設定 =====
# 本地排程已改為從 schedule_config.json 動態讀取
# 預設值與修改方式請參考 schedule_config.py

# GitHub Actions 排程（UTC 時間 → 台灣時間 = UTC+8）
# 對應 .github/workflows/auto-checkin.yml 中的 cron 設定
GITHUB_ACTIONS_SCHEDULE = [
    # (UTC開始, UTC結束, 動作, 台灣時間說明)
    ("00:30", "01:15", "上班", "08:30-09:15"),
    ("03:50", "04:15", "午休下班", "11:50-12:15"),
    ("04:50", "05:15", "午休上班", "12:50-13:15"),
    ("09:40", "11:00", "下班", "17:40-19:00"),
]


def main():
    """主程式入口"""
    print("🔔 自動打卡程式啟動...")
    print("💡 提示:")
    print("   - 使用 'python main.py test' 來測試打卡記錄解析")
    print("   - 使用 'python main.py debug' 來調試 HTML 結構")
    print("   - 使用 'python main.py email' 來測試寄信功能")
    print("   - 使用 'python main.py hours' 來計算今天滿8小時的下班時間")
    print("   - 使用 'python main.py force <動作>' 來強制打卡")
    print("   - 使用 'python main.py auto' 來自動偵測下班時間並打卡")
    print("   - 使用 'python main.py vpn' 來測試 VPN 連線狀態")
    print("   - 使用 'python main.py login' 來測試登入功能")
    print("   - 使用 'python main.py telegram' 來測試 Telegram 通知")
    print("   - 使用 'python main.py status' 來查詢當前打卡狀態 (推送到 Telegram)")
    print("   - 使用 'python main.py bot' 來啟動互動式 Telegram Bot (手機可下指令)")

    # 顯示當前時間資訊
    current_time = datetime.datetime.now()
    print(f"🕐 當前本地時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if os.getenv("GITHUB_ACTIONS"):
        taiwan_time = current_time + datetime.timedelta(hours=8)
        print(f"🌏 對應台灣時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("💻 本地環境，使用本地時間")

    # 檢查是否在 GitHub Actions 環境中
    if os.getenv("GITHUB_ACTIONS"):
        print("🤖 檢測到 GitHub Actions 環境，執行單次打卡檢查...")
        current_time = datetime.datetime.now().strftime("%H:%M")
        print(f"⏰ 當前時間 (UTC): {current_time}")

        # 判斷打卡來源
        checkin_source = "GitHub Actions 手動觸發" if os.getenv(
            "GITHUB_EVENT_NAME") == "workflow_dispatch" else "GitHub Actions 排程"

        # 根據當前時間判斷應該執行哪個打卡動作（UTC 時間）
        # 台灣時間 08:30 = UTC 00:30
        if current_time >= "00:30" and current_time <= "01:15":
            print("🕘 執行上班打卡 (台灣時間 08:45)")
            run_checkin("上班", source=checkin_source)
        # 台灣時間 11:50 = UTC 03:50
        elif current_time >= "03:50" and current_time <= "04:15":
            print("🕘 執行午休下班打卡 (台灣時間 12:00)")
            run_checkin("午休下班", source=checkin_source)
        # 台灣時間 12:50 = UTC 04:50
        elif current_time >= "04:50" and current_time <= "05:15":
            print("🕘 執行午休上班打卡 (台灣時間 13:00)")
            run_checkin("午休上班", source=checkin_source)
        # 台灣時間 17:45 = UTC 09:45
        elif current_time >= "09:40" and current_time <= "11:00":
            print("🕘 執行下班打卡 (台灣時間 17:45)")
            run_checkin("下班", source=checkin_source)
        # 台灣時間 18:30 = UTC 10:00
        # elif current_time >= "11:00" and current_time <= "11:15":
        #     print("🕘 執行下班打卡 (台灣時間 19:00)")
        #     run_checkin("下班")
        else:
            print(f"⏸ 當前時間 {current_time} UTC 不在打卡時間範圍內")
            print("📅 打卡時間表:")
            print("   - 上班: 00:30-01:15 UTC (台灣 08:30-09:15)")
            print("   - 午休下班: 03:50-04:15 UTC (台灣 11:50-12:15)")
            print("   - 午休上班: 04:50-05:15 UTC (台灣 12:50-13:15)")
            print("   - 下班: 09:40-11:00 UTC (台灣 17:40-19:00)")
            print("⏸ 跳過執行，等待下次排程時間")
    else:
        print("💻 本地環境，啟動排程模式...")
        setup_schedule()

        while True:
            schedule.run_pending()
            time.sleep(1)


def run_checkin(label, source=None, use_vpn=None):
    """執行打卡動作
    
    Args:
        label: 打卡標籤（上班、下班等）
        source: 打卡來源
        use_vpn: 是否使用 VPN，None 表示自動判斷（本地環境使用）
    """
    # 判斷是否需要 VPN（本地環境預設使用，GitHub Actions 不使用）
    if use_vpn is None:
        use_vpn = not os.getenv("GITHUB_ACTIONS") and os.getenv("VPN_HOST")
    
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    
    try:
        # 嘗試連接 VPN（如果需要）
        if use_vpn:
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試打卡...")
                # 通知 VPN 連接失敗
                TelegramService.send_message(
                    f"⚠️ <b>VPN 連接失敗</b>\n動作: {label}\n仍會嘗試打卡..."
                )
        
        automation.setup_driver()
        if automation.login():
            automation.punch_in(label)
        else:
            # 登入失敗也要通知
            TelegramService.send_checkin_notification(
                "登入失敗", label, source=source
            )
    except Exception as e:
        print(f"❌ 打卡過程出錯: {e}")
        EmailService.send_checkin_notification(
            f"打卡失敗: {e}", label, source=source)
        TelegramService.send_checkin_notification(
            f"打卡失敗: {e}", label, source=source
        )
    finally:
        automation.quit()
        # 斷開 VPN（如果有連接）
        if vpn and vpn_connected:
            vpn.disconnect()


def setup_schedule():
    """設置本地排程"""     
    # 檢查是否為工作日
    if not Config.is_workday():
        print("📅 今天不是工作日，跳過排程設置")
        return

    # 檢查是否為請假日
    if Config.is_skip_today():
        return

    # 檢查自動打卡是否啟用
    if not Config.AUTO_CHECKIN_ENABLED:
        print("⏸ 自動打卡已停用")
        return

    print("⏰ 設置排程...")
    schedule_times = schedule_config.get_schedule_as_tuples()
    for time_str, label in schedule_times:
        schedule.every().day.at(time_str).do(
            lambda l=label: run_checkin(l, source="本地環境")
        )
        print(f"   {time_str} - {label}")
    print("✅ 排程設置完成")


def reload_schedule():
    """重新載入排程（在 schedule 模式中呼叫，重新註冊所有 job）"""
    schedule.clear()
    schedule_times = schedule_config.get_schedule_as_tuples()
    for time_str, label in schedule_times:
        schedule.every().day.at(time_str).do(
            lambda l=label: run_checkin(l, source="本地環境")
        )
    print(f"🔄 排程已重新載入 ({len(schedule_times)} 個項目)")


def test_mode():
    """測試模式"""
    vpn = None
    vpn_connected = False
    try:
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試執行...")
        
        automation = WebAutomation()
        automation.test_attendance_records()
    finally:
        if vpn and vpn_connected:
            vpn.disconnect()


def debug_mode():
    """調試模式"""
    vpn = None
    vpn_connected = False
    try:
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試執行...")
        
        automation = WebAutomation()
        automation.debug_html_structure()
    finally:
        if vpn and vpn_connected:
            vpn.disconnect()


def email_test_mode():
    """寄信測試模式"""
    EmailService.test_email()


def calculate_work_hours_mode():
    """計算工時模式"""
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    
    try:
        # 嘗試連接 VPN（如果設定了 VPN_HOST）
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試執行...")
        
        automation.setup_driver()
        if automation.login():
            print("✅ 登入成功，開始計算工時...")
            automation.calculate_work_hours()
        else:
            print("❌ 登入失敗，無法計算工時")
    except Exception as e:
        print(f"❌ 計算工時過程出錯: {e}")
    finally:
        automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()


def force_punch_mode():
    """強制打卡模式"""
    if len(sys.argv) < 3:
        print("❌ 請指定打卡動作")
        print("💡 用法: python main.py force <動作>")
        print("   可用動作: 上班, 午休下班, 午休上班, 下班")
        return
    
    action = sys.argv[2]
    valid_actions = ["上班", "午休下班", "午休上班", "下班"]
    
    if action not in valid_actions:
        print(f"❌ 無效的打卡動作: {action}")
        print(f"💡 可用動作: {', '.join(valid_actions)}")
        return
    
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    
    try:
        # 嘗試連接 VPN（如果設定了 VPN_HOST）
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試打卡...")
        
        automation.setup_driver()
        if automation.login():
            print(f"✅ 登入成功，開始強制打卡: {action}")
            success = automation.force_punch(action)
            if success:
                print(f"🎉 {action} 打卡完成")
            else:
                print(f"❌ {action} 打卡失敗")
        else:
            print("❌ 登入失敗，無法執行強制打卡")
    except Exception as e:
        print(f"❌ 強制打卡過程出錯: {e}")
    finally:
        automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()


def auto_checkout_mode():
    """自動下班偵測模式"""
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    
    try:
        # 嘗試連接 VPN（如果設定了 VPN_HOST）
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試執行...")
        
        automation.setup_driver()
        if automation.login():
            print("✅ 登入成功，開始自動下班偵測...")
            success = automation.auto_checkout_when_ready()
            if success:
                print("🎉 自動下班打卡完成")
            else:
                print("❌ 自動下班打卡失敗")
        else:
            print("❌ 登入失敗，無法執行自動下班偵測")
    except Exception as e:
        print(f"❌ 自動下班偵測過程出錯: {e}")
    finally:
        automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()


def login_test_mode():
    """登入測試模式 - 測試登入並檢查打卡按鈕"""
    from selenium.webdriver.common.by import By
    
    print("🔐 登入測試模式")
    print("=" * 50)
    
    # 顯示當前設定
    print("📋 登入設定:")
    print(f"   USERNAME: {Config.USERNAME if Config.USERNAME else '❌ 未設定'}")
    print(f"   PASSWORD: {'✅ 已設定' if Config.PASSWORD else '❌ 未設定'}")
    print(f"   LOGIN_URL: {Config.LOGIN_URL if Config.LOGIN_URL else '❌ 未設定'}")
    print()
    
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    test_results = {
        "vpn": None,
        "browser": False,
        "login": False,
        "buttons": False,
    }
    
    try:
        # 步驟 1: 嘗試連接 VPN
        if os.getenv("VPN_HOST"):
            print("🔌 步驟 1/4: 連接 VPN...")
            vpn = VPNService()
            vpn_connected = vpn.connect()
            test_results["vpn"] = vpn_connected
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試登入...")
            print()
        else:
            print("ℹ️ 步驟 1/4: 未設定 VPN，跳過")
            print()
        
        # 步驟 2: 啟動瀏覽器
        print("🌐 步驟 2/4: 啟動瀏覽器...")
        automation.setup_driver()
        test_results["browser"] = True
        print("✅ 瀏覽器啟動成功")
        print()
        
        # 步驟 3: 嘗試登入
        print("🔐 步驟 3/4: 嘗試登入...")
        login_start = time.time()
        login_success = automation.login()
        login_elapsed = time.time() - login_start
        test_results["login"] = login_success
        
        if not login_success:
            print(f"❌ 登入失敗（耗時 {login_elapsed:.1f} 秒）")
            return
        
        print(f"✅ 登入成功（耗時 {login_elapsed:.1f} 秒）")
        print()
        
        # 步驟 4: 檢測打卡按鈕
        print("🔘 步驟 4/4: 檢測打卡按鈕...")
        time.sleep(2)  # 等待頁面完全載入
        
        # 找出所有打卡相關按鈕
        check_in_buttons = automation.driver.find_elements(
            By.XPATH, "//button[contains(text(),'Check in')]"
        )
        check_out_buttons = automation.driver.find_elements(
            By.XPATH, "//button[contains(text(),'Check out')]"
        )
        all_check_buttons = automation.driver.find_elements(
            By.XPATH, "//button[contains(text(),'Check')]"
        )
        
        print(f"   - Check in 按鈕: {len(check_in_buttons)} 個")
        print(f"   - Check out 按鈕: {len(check_out_buttons)} 個")
        print(f"   - 所有 Check 相關按鈕: {len(all_check_buttons)} 個")
        
        if all_check_buttons:
            test_results["buttons"] = True
            print()
            print("📋 按鈕詳細資訊:")
            for i, btn in enumerate(all_check_buttons, 1):
                btn_text = btn.text.strip()
                is_enabled = btn.is_enabled()
                is_displayed = btn.is_displayed()
                status = []
                if is_displayed:
                    status.append("顯示中")
                if is_enabled:
                    status.append("可點擊")
                else:
                    status.append("已停用")
                print(f"   {i}. 文字: '{btn_text}' | 狀態: {', '.join(status)}")
            
            # 判斷當前打卡狀態
            print()
            print("🎯 當前打卡狀態判斷:")
            if check_in_buttons and not check_out_buttons:
                print("   📍 尚未上班打卡（顯示 Check in 按鈕）")
            elif check_out_buttons and not check_in_buttons:
                print("   📍 已上班，可以下班打卡（顯示 Check out 按鈕）")
            elif check_in_buttons and check_out_buttons:
                print("   📍 同時顯示 Check in 和 Check out 按鈕")
            
            # 嘗試獲取打卡記錄
            print()
            print("📅 嘗試獲取今日打卡記錄...")
            try:
                from attendance_parser import AttendanceParser
                records = AttendanceParser.get_today_attendance_records(automation.driver)
                if records:
                    print(f"✅ 找到 {len(records)} 筆打卡記錄")
                    for i, record in enumerate(records, 1):
                        check_in = record.get('check_in', '無')
                        check_out = record.get('check_out', '無')
                        print(f"   {i}. Check in: {check_in} | Check out: {check_out}")
                else:
                    print("ℹ️ 今日尚無打卡記錄")
            except Exception as e:
                print(f"⚠️ 無法獲取打卡記錄: {e}")
        else:
            print("❌ 找不到任何打卡按鈕")
            print("💡 可能的原因:")
            print("   - 網站結構已變更")
            print("   - 頁面尚未完全載入")
            print("   - 帳號權限問題")
        
    except Exception as e:
        print(f"❌ 登入測試過程出錯: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 顯示測試總結
        print()
        print("=" * 50)
        print("📊 測試結果總結:")
        if test_results["vpn"] is not None:
            print(f"   {'✅' if test_results['vpn'] else '❌'} VPN 連接")
        print(f"   {'✅' if test_results['browser'] else '❌'} 瀏覽器啟動")
        print(f"   {'✅' if test_results['login'] else '❌'} 登入系統")
        print(f"   {'✅' if test_results['buttons'] else '❌'} 偵測打卡按鈕")
        print()
        
        all_critical_passed = (
            test_results["browser"] 
            and test_results["login"] 
            and test_results["buttons"]
        )
        
        if all_critical_passed:
            print("🎉 所有測試通過！自動打卡功能應可正常運作")
        else:
            print("⚠️ 部分測試失敗，請檢查上方錯誤訊息")
        print("=" * 50)
        
        automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()


def telegram_test_mode():
    """Telegram 測試模式"""
    import requests
    
    print("📱 Telegram 通知測試")
    print("=" * 50)
    
    # 檢查設定
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    print("📋 Telegram 設定:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ 已設定' if token else '❌ 未設定'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅ 已設定' if chat_id else '❌ 未設定'}")
    print()
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN 未設定，請先在 .env 加入:")
        print("   TELEGRAM_BOT_TOKEN=你的_bot_token")
        return
    
    # 如果沒有 chat_id，幫忙找
    if not chat_id:
        print("🔍 TELEGRAM_CHAT_ID 未設定，正在嘗試自動偵測...")
        print()
        print("📝 請按照以下步驟操作:")
        print("   1. 在 Telegram 找到你的 bot")
        print("   2. 點 [Start] 或對 bot 傳送任何訊息（例如：hi）")
        print("   3. 完成後按 Enter 繼續...")
        input("   按 Enter 繼續> ")
        print()
        
        # 呼叫 getUpdates API
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ API 呼叫失敗: {response.status_code}")
                print(f"   回應: {response.text}")
                if response.status_code == 401:
                    print("💡 Token 可能不正確，請檢查 TELEGRAM_BOT_TOKEN")
                return
            
            data = response.json()
            
            if not data.get("ok"):
                print(f"❌ API 錯誤: {data.get('description', '未知錯誤')}")
                return
            
            updates = data.get("result", [])
            
            if not updates:
                print("❌ 找不到任何訊息")
                print()
                print("💡 請確認:")
                print("   1. 你已經在 Telegram 點選了 bot 並發送訊息")
                print("   2. Bot Token 正確")
                print("   3. 重新執行: python main.py telegram")
                return
            
            # 收集所有不同的 chat_id
            found_chats = {}
            for update in updates:
                msg = update.get("message") or update.get("edited_message") or {}
                chat = msg.get("chat", {})
                cid = chat.get("id")
                if cid:
                    name = chat.get("first_name", "") or chat.get("title", "Unknown")
                    chat_type = chat.get("type", "unknown")
                    found_chats[cid] = f"{name} ({chat_type})"
            
            if not found_chats:
                print("❌ 找不到 chat_id，請確認已對 bot 發送訊息")
                return
            
            print(f"✅ 找到 {len(found_chats)} 個 chat:")
            print()
            for cid, name in found_chats.items():
                print(f"   🆔 Chat ID: {cid}")
                print(f"   👤 Name: {name}")
                print()
            
            # 自動寫入 .env
            if len(found_chats) == 1:
                cid = list(found_chats.keys())[0]
                print(f"💡 自動將 chat_id ({cid}) 寫入 .env...")
                
                env_path = os.path.join(os.path.dirname(__file__), ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        content = f.read()
                    
                    if "TELEGRAM_CHAT_ID=" in content:
                        # 替換現有的設定
                        import re
                        new_content = re.sub(
                            r"TELEGRAM_CHAT_ID=.*",
                            f"TELEGRAM_CHAT_ID={cid}",
                            content
                        )
                    else:
                        # 加到檔案最後
                        new_content = content.rstrip() + f"\nTELEGRAM_CHAT_ID={cid}\n"
                    
                    with open(env_path, "w") as f:
                        f.write(new_content)
                    
                    print("✅ 已寫入 .env")
                    print()
                    print("🔄 請重新執行: python main.py telegram")
                else:
                    print(f"⚠️ 找不到 .env 檔案，請手動加入: TELEGRAM_CHAT_ID={cid}")
            else:
                print("⚠️ 找到多個 chat_id，請手動選擇並加到 .env")
            
            return
            
        except Exception as e:
            print(f"❌ 偵測失敗: {e}")
            return
    
    print("📤 發送測試訊息...")
    if TelegramService.test_connection():
        print("✅ 測試成功！請查看你的 Telegram")
    else:
        print("❌ 測試失敗")


def status_mode():
    """查詢當前打卡狀態並推送到 Telegram"""
    from selenium.webdriver.common.by import By
    from attendance_parser import AttendanceParser
    
    print("📊 查詢當前打卡狀態...")
    
    vpn = None
    vpn_connected = False
    automation = WebAutomation()
    
    try:
        # 嘗試連接 VPN
        if os.getenv("VPN_HOST"):
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試查詢...")
        
        automation.setup_driver()
        if not automation.login():
            print("❌ 登入失敗")
            TelegramService.send_message(
                "❌ <b>查詢失敗</b>\n登入打卡系統失敗"
            )
            return
        
        print("✅ 登入成功，正在獲取打卡記錄...")
        time.sleep(2)
        
        # 獲取打卡記錄
        records = AttendanceParser.get_today_attendance_records(automation.driver)
        
        # 獲取當前按鈕狀態
        check_in_buttons = automation.driver.find_elements(
            By.XPATH, "//button[contains(text(),'Check in')]"
        )
        check_out_buttons = automation.driver.find_elements(
            By.XPATH, "//button[contains(text(),'Check out')]"
        )
        
        # 判斷當前狀態
        if check_in_buttons:
            current_status = "🔵 尚未上班 / 已下班"
        elif check_out_buttons:
            current_status = "🟢 工作中（已上班，可下班）"
        else:
            current_status = "❓ 無法判斷"
        
        # 計算工時：將每筆 (check_out - check_in) 累加，並把進行中的工時段也納入
        work_hours = None
        first_check_in = None
        last_check_out = None
        if records:
            first_check_in = records[0].get('check_in')
            for record in records:
                if record.get('check_out'):
                    last_check_out = record['check_out']

            try:
                work_hours = AttendanceParser.calculate_work_hours(records)
            except Exception as e:
                print(f"⚠️ 計算工時失敗: {e}")
        
        # 顯示在終端
        print()
        print(f"狀態: {current_status}")
        if first_check_in:
            print(f"上班時間: {first_check_in}")
        if last_check_out:
            print(f"最後下班時間: {last_check_out}")
        if work_hours is not None:
            print(f"已工作: {work_hours:.1f} 小時")
        if records:
            print(f"打卡記錄: {len(records)} 筆")
        
        # 發送到 Telegram
        now = datetime.datetime.now()
        message_parts = [
            "📊 <b>打卡狀態查詢</b>",
            "",
            f"📅 <b>日期:</b> {now.strftime('%Y-%m-%d')}",
            f"⏰ <b>查詢時間:</b> {now.strftime('%H:%M:%S')}",
            "",
            f"<b>當前狀態:</b> {current_status}",
        ]
        
        if first_check_in:
            message_parts.append(f"🕘 <b>上班時間:</b> {first_check_in}")
        if last_check_out:
            message_parts.append(f"🕔 <b>最後下班時間:</b> {last_check_out}")
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
        TelegramService.send_message(message)
        
    except Exception as e:
        print(f"❌ 查詢狀態出錯: {e}")
        TelegramService.send_message(
            f"❌ <b>查詢失敗</b>\n{e}"
        )
    finally:
        automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()


def bot_mode():
    """Telegram Bot 互動模式 - 接收指令並回應"""
    print("🤖 啟動 Telegram Bot 互動模式")
    print("=" * 50)
    
    if not TelegramService.is_enabled():
        print("❌ Telegram 未設定，無法啟動 Bot")
        return
    
    bot = TelegramBotListener()
    
    # ===== 註冊指令 =====
    
    def cmd_help(args):
        """顯示幫助訊息（不可取消，立即回應）"""
        help_msg = (
            "📖 <b>可用指令</b>\n"
            "\n"
            "<b>📊 查詢類:</b>\n"
            "/status - 查詢當前打卡狀態\n"
            "/hours - 計算今天滿8小時的下班時間\n"
            "/schedule - 查看排程時間\n"
            "/current - 查看當前執行中的任務\n"
            "\n"
            "<b>🎯 打卡類:</b>\n"
            "/checkin - 強制執行上班打卡\n"
            "/checkout - 強制執行下班打卡\n"
            "/lunch_out - 執行午休下班打卡\n"
            "/lunch_in - 執行午休上班打卡\n"
            "/auto - 自動偵測下班時間並打卡\n"
            "\n"
            "<b>⏰ 排程設定:</b>\n"
            "/schedule_set &lt;動作&gt; &lt;時間&gt; - 修改排程時間\n"
            "  例: <code>/schedule_set 上班 08:45</code>\n"
            "/schedule_reset - 重置為預設排程\n"
            "\n"
            "<b>🛑 控制類:</b>\n"
            "/cancel - 取消當前任務\n"
            "/help - 顯示此幫助訊息"
        )
        TelegramService.send_message(help_msg)
    
    def cmd_schedule(args):
        """顯示當前排程時間（不可取消，立即回應）"""
        now = datetime.datetime.now()
        today_weekday = now.weekday()
        weekday_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
        is_workday = today_weekday in Config.WORK_DAYS
        is_skip = Config.is_skip_today()
        
        lines = [
            "📅 <b>打卡排程時間表</b>",
            "",
            f"🕐 當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')} ({weekday_names[today_weekday]})",
            f"📆 工作日: {'✅ 是' if is_workday else '❌ 否'}",
            f"🏖 請假日: {'✅ 是' if is_skip else '❌ 否'}",
            f"⚙️ 自動打卡: {'✅ 啟用' if Config.AUTO_CHECKIN_ENABLED else '❌ 停用'}",
            "",
            "<b>💻 本地環境排程 (台灣時間):</b>",
        ]
        
        # 從 JSON 動態讀取排程
        schedule_times = schedule_config.get_schedule_as_tuples()
        for time_str, label in schedule_times:
            try:
                hour, minute = map(int, time_str.split(":"))
                schedule_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if schedule_dt > now:
                    diff = schedule_dt - now
                    total_minutes = int(diff.total_seconds() / 60)
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    if hours > 0:
                        time_remaining = f"{hours}小時{minutes}分後"
                    else:
                        time_remaining = f"{minutes}分鐘後"
                    status = f"⏳ {time_remaining}"
                else:
                    status = "✅ 已過"
                
                lines.append(f"  {time_str} - {label} ({status})")
            except Exception:
                lines.append(f"  {time_str} - {label}")
        
        lines.append("")
        lines.append("<b>☁️ GitHub Actions 排程 (UTC → 台灣時間):</b>")
        for utc_start, utc_end, action, tw_time in GITHUB_ACTIONS_SCHEDULE:
            lines.append(f"  {utc_start}-{utc_end} UTC ({tw_time}) - {action}")
        
        lines.append("")
        lines.append("ℹ️ 排程僅在工作日（週一至週五）執行")
        lines.append("")
        lines.append("<b>✏️ 修改排程:</b>")
        lines.append("/schedule_set &lt;動作&gt; &lt;時間&gt;")
        lines.append("例: <code>/schedule_set 上班 08:45</code>")
        lines.append("/schedule_reset - 重置為預設值")
        
        TelegramService.send_message("\n".join(lines))
    
    def cmd_schedule_set(args):
        """修改排程時間
        用法: /schedule_set <動作> <時間>
        例: /schedule_set 上班 08:45
        """
        if not args:
            TelegramService.send_message(
                "❌ <b>用法錯誤</b>\n\n"
                "格式: /schedule_set &lt;動作&gt; &lt;時間&gt;\n\n"
                "<b>動作:</b> 上班、午休下班、午休上班、下班\n"
                "<b>時間:</b> HH:MM (24小時制)\n\n"
                "<b>範例:</b>\n"
                "<code>/schedule_set 上班 08:45</code>\n"
                "<code>/schedule_set 下班 18:30</code>"
            )
            return
        
        parts = args.split()
        if len(parts) != 2:
            TelegramService.send_message(
                "❌ <b>參數數量錯誤</b>\n"
                "需要 2 個參數: 動作 和 時間\n"
                "例: <code>/schedule_set 上班 08:45</code>"
            )
            return
        
        label, new_time = parts
        success, message = schedule_config.update_schedule_time(label, new_time)
        
        if success:
            # 顯示更新後的排程
            schedule_times = schedule_config.get_schedule_as_tuples()
            schedule_text = "\n".join(
                [f"  {t} - {l}" for t, l in schedule_times]
            )
            TelegramService.send_message(
                f"{message}\n\n"
                f"<b>當前排程:</b>\n{schedule_text}\n\n"
                f"⚠️ 如果排程模式（python main.py）正在執行，"
                f"需要重啟才會生效"
            )
        else:
            TelegramService.send_message(f"❌ {message}")
    
    def cmd_schedule_reset(args):
        """重置排程為預設值"""
        if schedule_config.reset_schedule():
            schedule_times = schedule_config.get_schedule_as_tuples()
            schedule_text = "\n".join(
                [f"  {t} - {l}" for t, l in schedule_times]
            )
            TelegramService.send_message(
                f"✅ <b>排程已重置為預設值</b>\n\n"
                f"<b>預設排程:</b>\n{schedule_text}\n\n"
                f"⚠️ 如果排程模式（python main.py）正在執行，"
                f"需要重啟才會生效"
            )
        else:
            TelegramService.send_message("❌ 重置排程失敗")
    
    def _connect_and_login(reporter):
        """共用：連接 VPN + 開瀏覽器 + 登入。回傳 (automation, vpn, vpn_connected)"""
        vpn = None
        vpn_connected = False
        automation = WebAutomation()
        
        # Step: VPN
        if os.getenv("VPN_HOST"):
            reporter.step("🔌 連接 VPN")
            vpn = VPNService()
            vpn_connected = vpn.connect()
            if not vpn_connected:
                print("⚠️ VPN 連接失敗，但仍會嘗試...")
        
        reporter.check_cancelled()
        
        # Step: Browser
        reporter.step("🌐 啟動瀏覽器")
        automation.setup_driver()
        
        reporter.check_cancelled()
        
        # Step: Login
        reporter.step("🔐 登入打卡系統")
        if not automation.login():
            raise Exception("登入打卡系統失敗")
        
        reporter.check_cancelled()
        
        return automation, vpn, vpn_connected
    
    def _cleanup(automation, vpn, vpn_connected):
        """共用清理"""
        if automation:
            automation.quit()
        if vpn and vpn_connected:
            vpn.disconnect()
    
    def cmd_status(args, reporter):
        """查詢當前打卡狀態"""
        from selenium.webdriver.common.by import By
        from attendance_parser import AttendanceParser
        
        automation = None
        vpn = None
        vpn_connected = False
        
        try:
            reporter.start("🔌 準備連接")
            automation, vpn, vpn_connected = _connect_and_login(reporter)
            
            reporter.step("📥 抓取打卡記錄")
            time.sleep(2)
            records = AttendanceParser.get_today_attendance_records(automation.driver)
            
            reporter.check_cancelled()
            
            reporter.step("🔘 偵測按鈕狀態")
            check_in_buttons = automation.driver.find_elements(
                By.XPATH, "//button[contains(text(),'Check in')]"
            )
            check_out_buttons = automation.driver.find_elements(
                By.XPATH, "//button[contains(text(),'Check out')]"
            )
            
            if check_in_buttons:
                current_status = "🔵 尚未上班 / 已下班"
            elif check_out_buttons:
                current_status = "🟢 工作中（已上班，可下班）"
            else:
                current_status = "❓ 無法判斷"
            
            # 計算工時：將每筆 (check_out - check_in) 累加，並把進行中的工時段也納入
            work_hours = None
            first_check_in = None
            last_check_out = None
            if records:
                first_check_in = records[0].get('check_in')
                for record in records:
                    if record.get('check_out'):
                        last_check_out = record['check_out']

                try:
                    work_hours = AttendanceParser.calculate_work_hours(records)
                except Exception:
                    pass
            
            # 完成並顯示結果
            now = datetime.datetime.now()
            summary_parts = [
                f"📅 <b>日期:</b> {now.strftime('%Y-%m-%d')}",
                f"<b>狀態:</b> {current_status}",
            ]
            if first_check_in:
                summary_parts.append(f"🕘 <b>上班:</b> {first_check_in}")
            if last_check_out:
                summary_parts.append(f"🕔 <b>最後下班:</b> {last_check_out}")
            if work_hours is not None:
                summary_parts.append(f"⏱ <b>已工作:</b> {work_hours:.1f} 小時")
            if records:
                summary_parts.append("")
                summary_parts.append("<b>📝 今日打卡記錄:</b>")
                for i, r in enumerate(records, 1):
                    summary_parts.append(
                        f"  {i}. {r.get('check_in', '無')} ~ {r.get('check_out', '無')}"
                    )
            
            reporter.complete("\n".join(summary_parts))
            
        finally:
            _cleanup(automation, vpn, vpn_connected)
    
    def _force_punch_with_reporter(action: str, reporter):
        """強制打卡共用邏輯（嚴格檢查狀態）"""
        from selenium.webdriver.common.by import By
        from attendance_parser import AttendanceParser
        
        expected_button = {
            "上班": "Check in",
            "午休下班": "Check out",
            "午休上班": "Check in",
            "下班": "Check out",
        }
        
        automation = None
        vpn = None
        vpn_connected = False
        
        try:
            reporter.start("🔌 準備連接")
            automation, vpn, vpn_connected = _connect_and_login(reporter)
            
            reporter.step("🔍 檢查當前狀態")
            time.sleep(2)
            records = AttendanceParser.get_today_attendance_records(automation.driver)
            current_status = AttendanceParser.get_current_status(records)
            
            buttons = automation.driver.find_elements(
                By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]"
            )
            
            if not buttons:
                raise Exception("找不到打卡按鈕")
            
            current_btn_text = buttons[0].text.strip()
            expected = expected_button.get(action, "")
            
            reporter.check_cancelled()
            
            # 嚴格檢查：按鈕必須符合預期
            if expected not in current_btn_text:
                status_desc = {
                    "not_checked_in": "尚未上班",
                    "checked_in": "工作中（已上班）",
                    "checked_out": "已下班",
                }.get(current_status, current_status)
                
                suggestion = ""
                if "Check in" in current_btn_text:
                    suggestion = "\n💡 當前可執行: /checkin 或 /lunch_in"
                elif "Check out" in current_btn_text:
                    suggestion = "\n💡 當前可執行: /checkout 或 /lunch_out"
                
                error_msg = (
                    f"⚠️ 狀態與動作不符，已取消打卡\n\n"
                    f"📊 當前狀態: {status_desc}\n"
                    f"🔘 當前按鈕: {current_btn_text}\n"
                    f"❗ 你要執行: {action} (需要按鈕: {expected})"
                    f"{suggestion}"
                )
                reporter.fail(error_msg)
                return
            
            # 狀態合理，執行打卡
            reporter.step(f"🎯 執行 {action} 打卡")
            success = automation.force_punch(action)
            
            if success:
                reporter.complete(f"✅ <b>{action}打卡完成</b>")
            else:
                reporter.fail(f"{action}打卡失敗")
        
        finally:
            _cleanup(automation, vpn, vpn_connected)
    
    def cmd_checkin(args, reporter):
        """強制上班打卡"""
        _force_punch_with_reporter("上班", reporter)
    
    def cmd_checkout(args, reporter):
        """強制下班打卡"""
        _force_punch_with_reporter("下班", reporter)
    
    def cmd_lunch_out(args, reporter):
        """午休下班打卡"""
        _force_punch_with_reporter("午休下班", reporter)
    
    def cmd_lunch_in(args, reporter):
        """午休上班打卡"""
        _force_punch_with_reporter("午休上班", reporter)
    
    def cmd_hours(args, reporter):
        """計算工時"""
        automation = None
        vpn = None
        vpn_connected = False
        
        try:
            reporter.start("🔌 準備連接")
            automation, vpn, vpn_connected = _connect_and_login(reporter)
            
            reporter.step("📊 計算工時")
            automation.calculate_work_hours()
            
            reporter.complete("工時計算完成，請查看其他通知")
        finally:
            _cleanup(automation, vpn, vpn_connected)
    
    def cmd_auto(args, reporter):
        """自動下班偵測"""
        automation = None
        vpn = None
        vpn_connected = False
        
        try:
            reporter.start("🔌 準備連接")
            automation, vpn, vpn_connected = _connect_and_login(reporter)
            
            reporter.step("🤖 執行自動下班偵測")
            success = automation.auto_checkout_when_ready()
            
            if success:
                reporter.complete("✅ 自動下班打卡完成")
            else:
                reporter.fail("自動下班打卡失敗")
        finally:
            _cleanup(automation, vpn, vpn_connected)
    
    # 註冊所有指令
    bot.register_command("status", cmd_status)
    bot.register_command("checkin", cmd_checkin)
    bot.register_command("checkout", cmd_checkout)
    bot.register_command("lunch_out", cmd_lunch_out)
    bot.register_command("lunch_in", cmd_lunch_in)
    bot.register_command("hours", cmd_hours)
    bot.register_command("auto", cmd_auto)
    # 不可取消的指令（立即回應，沒有 reporter）
    bot.register_command("help", cmd_help, cancellable=False)
    bot.register_command("start", cmd_help, cancellable=False)
    bot.register_command("schedule", cmd_schedule, cancellable=False)
    bot.register_command("schedule_set", cmd_schedule_set, cancellable=False)
    bot.register_command("schedule_reset", cmd_schedule_reset, cancellable=False)
    
    print("📋 已註冊指令:")
    for cmd in bot.commands.keys():
        print(f"   /{cmd}")
    print()
    print("💡 提示: 在 Telegram 對話中輸入指令來操作")
    print("💡 按 Ctrl+C 停止 Bot")
    print()
    
    bot.start(blocking=True)


def vpn_test_mode():
    """VPN 連線測試模式"""
    from vpn_service import check_vpn_installed
    
    print("🔍 檢查 VPN 設定...")
    
    # 檢查 openfortivpn 是否安裝
    if not check_vpn_installed():
        print("❌ openfortivpn 未安裝")
        print("💡 安裝方式: brew install openfortivpn")
        return
    
    print("✅ openfortivpn 已安裝")
    
    # 檢查環境變數
    vpn_host = os.getenv("VPN_HOST")
    vpn_user = os.getenv("VPN_USERNAME")
    vpn_pass = os.getenv("VPN_PASSWORD")
    
    print(f"   VPN_HOST: {'✅ 已設定' if vpn_host else '❌ 未設定'}")
    print(f"   VPN_USERNAME: {'✅ 已設定' if vpn_user else '❌ 未設定'}")
    print(f"   VPN_PASSWORD: {'✅ 已設定' if vpn_pass else '❌ 未設定'}")
    
    vpn = VPNService()
    print(f"🔌 VPN 連線狀態: {'已連接' if vpn.is_connected() else '未連接'}")
    
    if vpn_host and vpn_user and vpn_pass:
        print("\n💡 執行 'python main.py vpn connect' 來測試連線")
    
    # 如果有 connect 參數，嘗試連線
    if len(sys.argv) > 2 and sys.argv[2] == "connect":
        print("\n🔌 嘗試連接 VPN...")
        if vpn.connect():
            print("✅ VPN 連線成功！")
            time.sleep(5)
            vpn.disconnect()
        else:
            print("❌ VPN 連線失敗")


if __name__ == "__main__":
    # 檢查是否為測試模式
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_mode()
        elif sys.argv[1] == "debug":
            debug_mode()
        elif sys.argv[1] == "email":
            email_test_mode()
        elif sys.argv[1] == "hours":
            calculate_work_hours_mode()
        elif sys.argv[1] == "force":
            force_punch_mode()
        elif sys.argv[1] == "auto":
            auto_checkout_mode()
        elif sys.argv[1] == "vpn":
            vpn_test_mode()
        elif sys.argv[1] == "login":
            login_test_mode()
        elif sys.argv[1] == "telegram":
            telegram_test_mode()
        elif sys.argv[1] == "status":
            status_mode()
        elif sys.argv[1] == "bot":
            bot_mode()
        else:
            print("❌ 未知的參數。可用參數: test, debug, email, hours, force, auto, vpn, login, telegram, status, bot")
    else:
        main()
