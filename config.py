"""
配置管理模組
處理環境變數和系統配置
"""
import os
import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    """系統配置類別"""
    
    # 基本配置
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")
    LOGIN_URL = os.getenv("LOGIN_URL")
    AUTO_CHECKIN_ENABLED = os.getenv("AUTO_CHECKIN_ENABLED", "true").lower() == "true"
    
    # 工作日設定 (0=週一, 6=週日)
    WORK_DAYS = [0, 1, 2, 3, 4]
    
    # 郵件配置
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    EMAIL_TO = os.getenv("EMAIL_TO")
    
    # 請假日設定
    SKIP_DATES = set()
    
    @classmethod
    def load_skip_dates(cls):
        """載入請假日設定"""
        skip_dates_str = os.getenv("SKIP_DATES", "")
        if skip_dates_str:
            for d in skip_dates_str.split(","):
                try:
                    cls.SKIP_DATES.add(datetime.datetime.strptime(d.strip(), "%Y-%m-%d").date())
                except ValueError:
                    print(f"⚠️ 無效日期格式: {d.strip()}，應為 YYYY-MM-DD")
    
    @classmethod
    def is_skip_today(cls):
        """檢查今天是否為請假日"""
        today = datetime.date.today()
        if today in cls.SKIP_DATES:
            print(f"⏸ 今天 {today} 在 SKIP_DATES，跳過自動打卡")
            return True
        return False
    
    @classmethod
    def is_workday(cls):
        """檢查今天是否為工作日"""
        today = datetime.date.today()
        return today.weekday() in cls.WORK_DAYS
    
    @classmethod
    def validate_config(cls):
        """驗證必要的配置是否完整"""
        required_vars = {
            "USERNAME": cls.USERNAME,
            "PASSWORD": cls.PASSWORD,
            "LOGIN_URL": cls.LOGIN_URL
        }
        
        missing_vars = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ 缺少必要的環境變數: {', '.join(missing_vars)}")
            return False
        
        return True

# 初始化配置
Config.load_skip_dates()
