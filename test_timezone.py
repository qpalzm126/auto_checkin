#!/usr/bin/env python3
"""
測試時區轉換功能
驗證 GitHub Actions 環境中的台灣時間顯示
"""
import os
import datetime
from email_service import EmailService

def test_timezone_conversion():
    """測試時區轉換"""
    print("🧪 開始測試時區轉換...")
    
    # 模擬本地環境
    print("\n📱 本地環境測試:")
    os.environ.pop("GITHUB_ACTIONS", None)  # 確保不在 GitHub Actions 環境
    
    # 測試 send_checkin_notification
    EmailService.send_checkin_notification(
        "測試結果", 
        "測試打卡", 
        work_hours=8.5,
        source="本地環境測試"
    )
    
    # 模擬 GitHub Actions 環境
    print("\n🤖 GitHub Actions 環境測試:")
    os.environ["GITHUB_ACTIONS"] = "true"
    
    # 測試 send_checkin_notification
    EmailService.send_checkin_notification(
        "測試結果", 
        "測試打卡", 
        work_hours=8.5,
        source="GitHub Actions 測試"
    )
    
    # 測試 test_email
    print("\n📧 測試寄信功能:")
    EmailService.test_email()
    
    print("\n✅ 時區轉換測試完成")

def show_time_comparison():
    """顯示時間比較"""
    print("\n🕐 時間比較:")
    
    # 當前 UTC 時間
    utc_now = datetime.datetime.now()
    print(f"UTC 時間: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 台灣時間 (UTC + 8)
    taiwan_time = utc_now + datetime.timedelta(hours=8)
    print(f"台灣時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 時差
    time_diff = taiwan_time - utc_now
    print(f"時差: {time_diff}")

if __name__ == "__main__":
    print("🔔 時區轉換測試程式啟動...")
    
    # 顯示時間比較
    show_time_comparison()
    
    # 測試時區轉換
    print("\n" + "="*50)
    print("是否要測試實際的郵件發送？(需要網路連接和郵件配置)")
    print("請執行: python test_timezone.py --test-email")
    
    import sys
    if "--test-email" in sys.argv:
        test_timezone_conversion()
    else:
        print("\n💡 提示: 要測試實際郵件發送，請加上 --test-email 參數")
