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
        msg = MIMEMultipart()
        msg['From'] = Config.SMTP_USER
        msg['To'] = Config.EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.send_message(msg)
            server.quit()
            print(f"📧 已寄出通知信: {subject}")
        except Exception as e:
            print(f"❌ 寄信失敗: {e}")

    @staticmethod
    def test_email():
        """測試寄信功能"""
        print("🧪 開始測試寄信功能...")
        
        # 檢查環境變數
        required_vars = ["SMTP_SERVER", "SMTP_USER", "SMTP_PASS", "EMAIL_TO"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(Config, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 缺少必要的環境變數: {', '.join(missing_vars)}")
            print("請在 .env 檔案中設定以下變數:")
            for var in missing_vars:
                print(f"  {var}=your_value")
            return False
        
        # 測試寄信
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"🧪 自動打卡系統測試信 - {current_time}"
        body = f"""
這是一封測試信，用於驗證自動打卡系統的寄信功能。

測試時間: {current_time}
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
    def send_checkin_notification(result, label, work_hours=None):
        """發送打卡通知郵件"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"📅 自動打卡通知 - {label} - {current_time}"
        
        body = f"""
自動打卡系統通知

時間: {current_time}
動作: {label}
結果: {result}
"""
        
        if work_hours is not None:
            body += f"工時: {work_hours:.2f} 小時\n"
        
        body += f"""
環境: {'GitHub Actions' if os.getenv('GITHUB_ACTIONS') else '本地環境'}

---
自動打卡系統
        """
        
        EmailService.send_email(subject, body)
