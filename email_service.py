"""
郵件服務模組
處理郵件發送和通知功能
"""
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


class EmailService:
    """郵件服務類別"""

    @staticmethod
    def send_email(subject, body):
        """發送郵件"""
        # 檢查環境變數
        if not all([Config.SMTP_SERVER, Config.SMTP_USER, Config.SMTP_PASS, Config.EMAIL_TO]):
            print("❌ 郵件配置不完整，跳過發送")
            return False

        print(f"📧 準備發送郵件...")
        print(f"   SMTP Server: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
        print(f"   From: {Config.SMTP_USER}")
        print(f"   To: {Config.EMAIL_TO}")

        msg = MIMEMultipart()
        msg['From'] = Config.SMTP_USER
        msg['To'] = Config.EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            print("🔌 連接到 SMTP 伺服器...")
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            print("🔐 啟動 TLS 加密...")
            server.starttls()
            print("🔑 登入 SMTP 伺服器...")
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            print("📤 發送郵件...")
            server.send_message(msg)
            server.quit()
            print(f"✅ 已寄出通知信: {subject}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP 認證失敗: {e}")
            print("💡 請檢查 SMTP_USER 和 SMTP_PASS 是否正確")
        except smtplib.SMTPConnectError as e:
            print(f"❌ SMTP 連線失敗: {e}")
            print("💡 請檢查 SMTP_SERVER 和 SMTP_PORT 是否正確")
        except smtplib.SMTPException as e:
            print(f"❌ SMTP 錯誤: {e}")
        except Exception as e:
            print(f"❌ 寄信失敗: {e}")
            print(f"   錯誤類型: {type(e).__name__}")
        return False

    @staticmethod
    def test_email():
        """測試寄信功能"""
        print("🧪 開始測試寄信功能...")

        # 檢查是否在 GitHub Actions 環境
        import os
        if os.getenv("GITHUB_ACTIONS"):
            print("🤖 檢測到 GitHub Actions 環境")
            print("⚠️  注意：某些 SMTP 服務商可能限制 GitHub Actions 的連線")

        # 檢查環境變數
        required_vars = ["SMTP_SERVER", "SMTP_USER", "SMTP_PASS", "EMAIL_TO"]
        missing_vars = []

        for var in required_vars:
            value = getattr(Config, var)
            if not value:
                missing_vars.append(var)
            else:
                # 隱藏敏感資訊
                if "PASS" in var:
                    print(f"✅ {var}: {'*' * len(str(value))}")
                else:
                    print(f"✅ {var}: {value}")

        if missing_vars:
            print(f"❌ 缺少必要的環境變數: {', '.join(missing_vars)}")
            print("請在 .env 檔案中設定以下變數:")
            for var in missing_vars:
                print(f"  {var}=your_value")
            return False

        # 測試寄信
        # 在 GitHub Actions 環境中顯示台灣時間，本地環境顯示本地時間
        if os.getenv("GITHUB_ACTIONS"):
            taiwan_time = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_time = taiwan_time.strftime("%Y-%m-%d %H:%M:%S")
            timezone_info = " (台灣時間)"
        else:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timezone_info = ""
        
        subject = f"🧪 自動打卡系統測試信 - {current_time}{timezone_info}"
        body = f"""
這是一封測試信，用於驗證自動打卡系統的寄信功能。

測試時間: {current_time}{timezone_info}
系統狀態: 正常運作
環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else '本地環境'}

如果您收到這封信，表示寄信功能運作正常！

---
自動打卡系統
        """

        try:
            EmailService.send_email(subject, body)
            print("✅ 測試寄信成功！")
            return True
        except Exception as e:
            print(f"❌ 測試寄信失敗: {e}")
            return False

    @staticmethod
    def send_checkin_notification(result, label, work_hours=None, source=None, attendance_records=None):
        """發送打卡通知郵件"""
        # 在 GitHub Actions 環境中顯示台灣時間，本地環境顯示本地時間
        if os.getenv("GITHUB_ACTIONS"):
            # GitHub Actions 使用 UTC 時間，台灣時間 = UTC + 8
            taiwan_time = datetime.datetime.now() + datetime.timedelta(hours=8)
            current_time = taiwan_time.strftime("%Y-%m-%d %H:%M:%S")
            timezone_info = " (台灣時間)"
        else:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timezone_info = ""
        
        subject = f"📅 自動打卡通知 - {label} - {current_time}{timezone_info}"

        # 判斷打卡來源
        if source is None:
            if os.getenv("GITHUB_ACTIONS"):
                # 檢查是否為手動觸發
                if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
                    source = "GitHub Actions 手動觸發"
                else:
                    source = "GitHub Actions 排程"
            else:
                source = "本地環境"

        body = f"""
自動打卡系統通知

時間: {current_time}{timezone_info}
動作: {label}
結果: {result}
來源: {source}
"""

        if work_hours is not None:
            body += f"工時: {work_hours:.2f} 小時\n"

        # 添加打卡記錄
        if attendance_records:
            body += f"\n📊 當天打卡記錄:\n"
            for i, record in enumerate(attendance_records, 1):
                check_in = record.get('check_in', 'N/A')
                check_out = record.get('check_out', 'N/A')
                if check_out == '':
                    check_out = '進行中'
                body += f"  記錄 {i}: {check_in} - {check_out}\n"

        body += f"""
環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else '本地環境'}

---
自動打卡系統
        """

        EmailService.send_email(subject, body)
