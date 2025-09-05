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


def main():
    """主程式入口"""
    print("🔔 自動打卡程式啟動...")
    print("💡 提示:")
    print("   - 使用 'python main.py test' 來測試打卡記錄解析")
    print("   - 使用 'python main.py debug' 來調試 HTML 結構")
    print("   - 使用 'python main.py email' 來測試寄信功能")

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

        # 根據當前時間判斷應該執行哪個打卡動作（UTC 時間）
        # 台灣時間 08:30 = UTC 00:30
        if current_time >= "00:30" and current_time <= "01:15":
            print("🕘 執行上班打卡 (台灣時間 08:45)")
            run_checkin("上班")
        # 台灣時間 11:50 = UTC 03:50
        elif current_time >= "03:50" and current_time <= "04:15":
            print("🕘 執行午休下班打卡 (台灣時間 12:00)")
            run_checkin("午休下班")
        # 台灣時間 12:50 = UTC 04:50
        elif current_time >= "04:50" and current_time <= "05:15":
            print("🕘 執行午休上班打卡 (台灣時間 13:00)")
            run_checkin("午休上班")
        # 台灣時間 17:45 = UTC 09:45
        elif current_time >= "09:40" and current_time <= "11:00":
            print("🕘 執行下班打卡 (台灣時間 17:45)")
            run_checkin("下班")
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


def run_checkin(label):
    """執行打卡動作"""
    automation = WebAutomation()
    try:
        automation.setup_driver()
        if automation.login():
            automation.punch_in(label)
    except Exception as e:
        print(f"❌ 打卡過程出錯: {e}")
        EmailService.send_checkin_notification(f"打卡失敗: {e}", label)
    finally:
        automation.quit()


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
    schedule.every().day.at("08:45").do(lambda: run_checkin("上班"))
    schedule.every().day.at("12:00").do(lambda: run_checkin("午休下班"))
    schedule.every().day.at("13:00").do(lambda: run_checkin("午休上班"))
    schedule.every().day.at("17:46").do(lambda: run_checkin("下班"))
    print("✅ 排程設置完成")


def test_mode():
    """測試模式"""
    automation = WebAutomation()
    automation.test_attendance_records()


def debug_mode():
    """調試模式"""
    automation = WebAutomation()
    automation.debug_html_structure()


def email_test_mode():
    """寄信測試模式"""
    EmailService.test_email()


if __name__ == "__main__":
    # 檢查是否為測試模式
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_mode()
        elif sys.argv[1] == "debug":
            debug_mode()
        elif sys.argv[1] == "email":
            email_test_mode()
        else:
            print("❌ 未知的參數。可用參數: test, debug, email")
    else:
        main()
