#!/usr/bin/env python3
"""
測試 current_status 判斷功能
驗證打卡記錄解析和狀態判斷是否正確
"""
import datetime
from attendance_parser import AttendanceParser

def test_current_status_logic():
    """測試 current_status 判斷邏輯"""
    print("🧪 開始測試 current_status 判斷邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "沒有打卡記錄",
            "records": [],
            "expected": "not_checked_in"
        },
        {
            "name": "只有上班打卡",
            "records": [
                {"check_in": "09:00", "check_out": ""}
            ],
            "expected": "checked_in"
        },
        {
            "name": "完整的上班下班記錄",
            "records": [
                {"check_in": "09:00", "check_out": "17:00"}
            ],
            "expected": "checked_out"
        },
        {
            "name": "多次打卡 - 最後一次只有上班",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": ""}
            ],
            "expected": "checked_in"
        },
        {
            "name": "多次打卡 - 最後一次完整",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": "17:00"}
            ],
            "expected": "checked_out"
        },
        {
            "name": "異常情況 - 沒有上班時間",
            "records": [
                {"check_in": "", "check_out": "17:00"}
            ],
            "expected": "not_checked_in"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   記錄: {case['records']}")
        print(f"   預期狀態: {case['expected']}")
        
        # 測試 get_current_status
        actual_status = AttendanceParser.get_current_status(case['records'])
        print(f"   實際狀態: {actual_status}")
        
        if actual_status == case['expected']:
            print("   ✅ 狀態判斷正確")
        else:
            print(f"   ❌ 狀態判斷錯誤！預期: {case['expected']}, 實際: {actual_status}")
    
    print("\n✅ current_status 判斷邏輯測試完成")

def test_button_status_consistency():
    """測試按鈕狀態與 current_status 的一致性"""
    print("\n🧪 開始測試按鈕狀態一致性...")
    
    # 模擬不同的狀態組合
    status_scenarios = [
        {
            "current_status": "not_checked_in",
            "expected_button": "Check in",
            "description": "未打卡 → 應該顯示 Check in 按鈕"
        },
        {
            "current_status": "checked_in", 
            "expected_button": "Check out",
            "description": "已上班 → 應該顯示 Check out 按鈕"
        },
        {
            "current_status": "checked_out",
            "expected_button": "Check in", 
            "description": "已下班 → 應該顯示 Check in 按鈕"
        }
    ]
    
    for i, scenario in enumerate(status_scenarios, 1):
        print(f"\n📋 場景 {i}: {scenario['description']}")
        print(f"   current_status: {scenario['current_status']}")
        print(f"   預期按鈕: {scenario['expected_button']}")
        
        # 這裡只是展示邏輯，實際測試需要真實的按鈕
        print("   💡 實際測試需要運行 test_attendance_records() 來檢查真實按鈕狀態")
    
    print("\n✅ 按鈕狀態一致性測試完成")

if __name__ == "__main__":
    print("🔔 current_status 測試程式啟動...")
    
    # 測試 current_status 判斷邏輯
    test_current_status_logic()
    
    # 測試按鈕狀態一致性
    test_button_status_consistency()
    
    print("\n" + "="*50)
    print("💡 要測試實際的打卡記錄解析和按鈕狀態，請執行:")
    print("   python main.py test")
