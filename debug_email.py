#!/usr/bin/env python3
"""
GitHub Actions 郵件診斷腳本
用於診斷在 GitHub Actions 環境中郵件發送失敗的原因
"""

import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def check_environment():
    """檢查環境變數和網路連線"""
    print("🔍 開始診斷 GitHub Actions 郵件問題...")
    print("=" * 50)
    
    # 檢查環境
    print("📋 環境資訊:")
    print(f"   Python 版本: {os.sys.version}")
    print(f"   GitHub Actions: {bool(os.getenv('GITHUB_ACTIONS'))}")
    print(f"   作業系統: {os.name}")
    
    # 檢查環境變數
    print("\n🔧 環境變數檢查:")
    email_vars = {
        "SMTP_SERVER": Config.SMTP_SERVER,
        "SMTP_PORT": Config.SMTP_PORT,
        "SMTP_USER": Config.SMTP_USER,
        "SMTP_PASS": Config.SMTP_PASS,
        "EMAIL_TO": Config.EMAIL_TO
    }
    
    missing_vars = []
    for var, value in email_vars.items():
        if value:
            if "PASS" in var:
                print(f"   ✅ {var}: {'*' * len(str(value))}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 缺少環境變數: {', '.join(missing_vars)}")
        return False
    
    return True

def test_network_connectivity():
    """測試網路連線"""
    print("\n🌐 網路連線測試:")
    
    if not Config.SMTP_SERVER:
        print("   ❌ SMTP_SERVER 未設定，無法測試連線")
        return False
    
    try:
        # 測試 DNS 解析
        print(f"   🔍 解析 SMTP 伺服器: {Config.SMTP_SERVER}")
        ip = socket.gethostbyname(Config.SMTP_SERVER)
        print(f"   ✅ DNS 解析成功: {ip}")
        
        # 測試 TCP 連線
        print(f"   🔌 測試 TCP 連線: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((Config.SMTP_SERVER, Config.SMTP_PORT))
        sock.close()
        
        if result == 0:
            print("   ✅ TCP 連線成功")
            return True
        else:
            print(f"   ❌ TCP 連線失敗 (錯誤碼: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"   ❌ DNS 解析失敗: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 連線測試失敗: {e}")
        return False

def test_smtp_connection():
    """測試 SMTP 連線和認證"""
    print("\n📧 SMTP 連線測試:")
    
    try:
        print("   🔌 連接到 SMTP 伺服器...")
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.set_debuglevel(1)  # 啟用除錯模式
        
        print("   🔐 啟動 TLS 加密...")
        server.starttls()
        
        print("   🔑 測試認證...")
        server.login(Config.SMTP_USER, Config.SMTP_PASS)
        
        print("   ✅ SMTP 連線和認證成功")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ SMTP 認證失敗: {e}")
        print("   💡 可能原因:")
        print("      - 使用者名稱或密碼錯誤")
        print("      - 需要啟用「應用程式密碼」")
        print("      - 帳號被鎖定或限制")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"   ❌ SMTP 連線失敗: {e}")
        print("   💡 可能原因:")
        print("      - SMTP 伺服器地址或端口錯誤")
        print("      - 防火牆阻擋連線")
        print("      - 網路連線問題")
        return False
        
    except smtplib.SMTPException as e:
        print(f"   ❌ SMTP 錯誤: {e}")
        return False
        
    except Exception as e:
        print(f"   ❌ 未預期的錯誤: {e}")
        return False

def test_email_sending():
    """測試實際發送郵件"""
    print("\n📤 郵件發送測試:")
    
    try:
        # 創建測試郵件
        msg = MIMEMultipart()
        msg['From'] = Config.SMTP_USER
        msg['To'] = Config.EMAIL_TO
        msg['Subject'] = "🧪 GitHub Actions 郵件測試"
        
        body = """
這是一封來自 GitHub Actions 的測試郵件。

如果您收到這封郵件，表示郵件功能運作正常。

測試時間: {time}
環境: GitHub Actions
        """.format(time=os.popen('date').read().strip())
        
        msg.attach(MIMEText(body, 'plain'))
        
        # 發送郵件
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        print("   ✅ 測試郵件發送成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 郵件發送失敗: {e}")
        return False

def main():
    """主診斷流程"""
    print("🚀 GitHub Actions 郵件診斷工具")
    print("=" * 50)
    
    # 步驟 1: 檢查環境變數
    if not check_environment():
        print("\n❌ 環境變數檢查失敗，請設定必要的環境變數")
        return
    
    # 步驟 2: 測試網路連線
    if not test_network_connectivity():
        print("\n❌ 網路連線測試失敗")
        return
    
    # 步驟 3: 測試 SMTP 連線
    if not test_smtp_connection():
        print("\n❌ SMTP 連線測試失敗")
        return
    
    # 步驟 4: 測試郵件發送
    if test_email_sending():
        print("\n🎉 所有測試通過！郵件功能運作正常")
    else:
        print("\n❌ 郵件發送測試失敗")
    
    print("\n💡 常見解決方案:")
    print("   1. 檢查 GitHub Secrets 是否正確設定")
    print("   2. 確認 SMTP 服務商是否支援 GitHub Actions")
    print("   3. 嘗試使用不同的 SMTP 服務商")
    print("   4. 檢查是否需要啟用「應用程式密碼」")

if __name__ == "__main__":
    main()
