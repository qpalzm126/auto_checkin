#!/usr/bin/env python3
"""
測試 Web 介面的基本功能
"""
import requests
import time
import subprocess
import sys
import os

def test_web_interface():
    """測試 Web 介面"""
    print("🧪 開始測試 Web 介面...")
    
    # 啟動 Flask 應用（在背景執行）
    print("🚀 啟動 Flask 應用...")
    process = subprocess.Popen([sys.executable, 'app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # 等待應用啟動
    time.sleep(3)
    
    try:
        # 測試首頁
        print("📱 測試首頁...")
        response = requests.get('http://localhost:5001', timeout=10)
        if response.status_code == 200:
            print("✅ 首頁載入成功")
        else:
            print(f"❌ 首頁載入失敗: {response.status_code}")
        
        # 測試日誌頁面
        print("📋 測試日誌頁面...")
        response = requests.get('http://localhost:5001/logs', timeout=10)
        if response.status_code == 200:
            print("✅ 日誌頁面載入成功")
        else:
            print(f"❌ 日誌頁面載入失敗: {response.status_code}")
        
        # 測試 API 端點
        print("🔌 測試 API 端點...")
        response = requests.get('http://localhost:5001/get_attendance_status', timeout=10)
        if response.status_code == 200:
            print("✅ 打卡狀態 API 正常")
        else:
            print(f"❌ 打卡狀態 API 失敗: {response.status_code}")
        
        print("🎉 Web 介面測試完成！")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路請求失敗: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
    finally:
        # 停止 Flask 應用
        print("⏹️ 停止 Flask 應用...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_web_interface()
