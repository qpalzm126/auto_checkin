#!/usr/bin/env python3
"""
自動打卡系統 Web 介面啟動腳本
"""
import os
import sys
import subprocess

def check_dependencies():
    """檢查依賴套件是否已安裝"""
    try:
        import flask
        print("✅ Flask 已安裝")
        return True
    except ImportError:
        print("❌ Flask 未安裝")
        return False

def install_dependencies():
    """安裝依賴套件"""
    print("📦 正在安裝依賴套件...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依賴套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依賴套件安裝失敗: {e}")
        return False

def main():
    """主程式"""
    print("🌐 自動打卡系統 Web 介面啟動器")
    print("=" * 50)
    
    # 檢查依賴
    if not check_dependencies():
        print("\n🔧 正在安裝缺少的依賴套件...")
        if not install_dependencies():
            print("❌ 無法安裝依賴套件，請手動執行: pip install -r requirements.txt")
            return
    
    # 檢查設定檔案
    if not os.path.exists('config.py'):
        print("❌ 找不到 config.py 設定檔案")
        print("請確保已正確設定 config.py 檔案")
        return
    
    print("\n🚀 啟動 Web 介面...")
    print("📱 請在瀏覽器中開啟: http://localhost:5001")
    print("⏹️  按 Ctrl+C 停止服務")
    print("=" * 50)
    
    # 啟動 Flask 應用
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Web 介面已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    main()
