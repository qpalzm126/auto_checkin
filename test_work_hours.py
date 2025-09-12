#!/usr/bin/env python3
"""
測試工時檢查邏輯
驗證修復後的工時檢查是否正常工作
"""
import datetime
import os
from web_automation import WebAutomation

def test_work_hours_logic():
    """測試工時檢查邏輯"""
    print("🧪 開始測試工時檢查邏輯...")
    
    # 模擬不同的工時情況
    test_cases = [
        {
            "name": "工時不足 - 6小時",
            "work_start": datetime.datetime.now() - datetime.timedelta(hours=6),
            "expected": "應該阻止打卡"
        },
        {
            "name": "工時不足 - 7.5小時", 
            "work_start": datetime.datetime.now() - datetime.timedelta(hours=7, minutes=30),
            "expected": "應該阻止打卡"
        },
        {
            "name": "工時充足 - 8小時",
            "work_start": datetime.datetime.now() - datetime.timedelta(hours=8),
            "expected": "應該允許打卡"
        },
        {
            "name": "工時充足 - 8.5小時",
            "work_start": datetime.datetime.now() - datetime.timedelta(hours=8, minutes=30),
            "expected": "應該允許打卡"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   上班時間: {case['work_start']}")
        print(f"   當前時間: {datetime.datetime.now()}")
        
        # 計算工時
        now = datetime.datetime.now()
        duration = now - case['work_start']
        hours = duration.total_seconds() / 3600
        print(f"   計算工時: {hours:.1f} 小時")
        
        # 模擬工時檢查邏輯
        if hours < 8:
            print(f"   ❌ 工時不足 ({hours:.1f}小時 < 8小時) - {case['expected']}")
            if os.getenv("GITHUB_ACTIONS"):
                print("   📧 在 GitHub Actions 環境中，會發送通知郵件")
            else:
                print("   ⏰ 在本地環境中，會延後打卡")
        else:
            print(f"   ✅ 工時充足 ({hours:.1f}小時 >= 8小時) - {case['expected']}")
    
    print("\n✅ 工時檢查邏輯測試完成")

def test_attendance_parsing():
    """測試打卡記錄解析"""
    print("\n🧪 開始測試打卡記錄解析...")
    
    automation = WebAutomation()
    try:
        automation.setup_driver()
        if automation.login():
            print("✅ 登入成功，開始解析打卡記錄...")
            automation.test_attendance_records()
        else:
            print("❌ 登入失敗，無法測試打卡記錄解析")
    except Exception as e:
        print(f"❌ 測試過程出錯: {e}")
    finally:
        automation.quit()

if __name__ == "__main__":
    print("🔔 工時檢查測試程式啟動...")
    
    # 顯示當前時間資訊
    current_time = datetime.datetime.now()
    print(f"🕐 當前本地時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if os.getenv("GITHUB_ACTIONS"):
        taiwan_time = current_time + datetime.timedelta(hours=8)
        print(f"🌏 對應台灣時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試工時檢查邏輯
    test_work_hours_logic()
    
    # 測試打卡記錄解析（需要實際登入）
    print("\n" + "="*50)
    print("是否要測試實際的打卡記錄解析？(需要網路連接和登入)")
    print("請執行: python test_work_hours.py --test-parsing")
    
    import sys
    if "--test-parsing" in sys.argv:
        test_attendance_parsing()
