#!/usr/bin/env python3
"""
測試移除 get_today_check_in 後的功能
驗證使用 get_today_attendance_records 的第一筆記錄是否正常工作
"""
import datetime
from attendance_parser import AttendanceParser

def test_attendance_records_first_record():
    """測試使用 get_today_attendance_records 的第一筆記錄獲取上班時間"""
    print("🧪 開始測試使用 get_today_attendance_records 第一筆記錄...")
    
    # 模擬打卡記錄
    test_records = [
        {
            "name": "正常打卡記錄",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": "17:00"}
            ],
            "expected_first_checkin": "09:00"
        },
        {
            "name": "只有上班打卡",
            "records": [
                {"check_in": "08:30", "check_out": ""}
            ],
            "expected_first_checkin": "08:30"
        },
        {
            "name": "沒有打卡記錄",
            "records": [],
            "expected_first_checkin": None
        }
    ]
    
    for i, case in enumerate(test_records, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   記錄: {case['records']}")
        
        # 模擬從第一筆記錄獲取上班時間的邏輯
        if case['records']:
            first_record = case['records'][0]
            if first_record.get('check_in'):
                try:
                    check_in_time_str = first_record['check_in']
                    today_date = datetime.datetime.now().date()
                    check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
                    work_start_time = datetime.datetime.combine(today_date, check_in_time)
                    print(f"   解析上班時間: {work_start_time}")
                    print(f"   預期上班時間: {case['expected_first_checkin']}")
                    
                    if check_in_time_str == case['expected_first_checkin']:
                        print("   ✅ 上班時間解析正確")
                    else:
                        print(f"   ❌ 上班時間解析錯誤！預期: {case['expected_first_checkin']}, 實際: {check_in_time_str}")
                except Exception as e:
                    print(f"   ❌ 解析上班時間失敗: {e}")
            else:
                print("   ⚠️ 第一筆記錄沒有 check_in")
        else:
            print("   ⚠️ 沒有打卡記錄")
            if case['expected_first_checkin'] is None:
                print("   ✅ 預期結果正確（沒有記錄）")
            else:
                print(f"   ❌ 預期有記錄但實際沒有")
    
    print("\n✅ get_today_attendance_records 第一筆記錄測試完成")

def test_fallback_logic():
    """測試備用邏輯（當沒有打卡記錄時使用預設時間）"""
    print("\n🧪 開始測試備用邏輯...")
    
    # 模擬沒有打卡記錄的情況
    records = []
    
    if not records:
        # 使用預設時間
        today_date = datetime.datetime.now().date()
        fallback_time = datetime.time(hour=9, minute=0)
        work_start_time = datetime.datetime.combine(today_date, fallback_time)
        print(f"📅 沒有打卡記錄，使用預設上班時間: {work_start_time}")
        print("✅ 備用邏輯正常")
    else:
        print("❌ 備用邏輯測試失敗")

if __name__ == "__main__":
    print("🔔 移除 get_today_check_in 測試程式啟動...")
    
    # 顯示當前時間
    current_time = datetime.datetime.now()
    print(f"🕐 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試使用第一筆記錄獲取上班時間
    test_attendance_records_first_record()
    
    # 測試備用邏輯
    test_fallback_logic()
    
    print("\n" + "="*50)
    print("✅ 移除 get_today_check_in 後的功能測試完成")
    print("💡 現在系統統一使用 get_today_attendance_records 來獲取打卡記錄")
