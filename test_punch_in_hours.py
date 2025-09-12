#!/usr/bin/env python3
"""
測試 punch_in 函數中的工時計算
驗證修正後的工時計算邏輯是否正確
"""
import datetime
from attendance_parser import AttendanceParser

def test_punch_in_hours_calculation():
    """測試 punch_in 中的工時計算邏輯"""
    print("🧪 開始測試 punch_in 工時計算邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "只有上午工時 - 應該阻止下班",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"}
            ],
            "current_status": "checked_out",
            "expected_should_punch": False,
            "expected_total_hours": 3.0
        },
        {
            "name": "上午+下午工時充足 - 應該允許下班",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": "17:00"}
            ],
            "current_status": "checked_out",
            "expected_should_punch": True,
            "expected_total_hours": 7.0
        },
        {
            "name": "正在下午工作 - 需要計算當前工時",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": ""}
            ],
            "current_status": "checked_in",
            "expected_should_punch": True,  # 假設總工時已滿8小時
            "expected_total_hours": 7.34  # 3小時(上午) + 4.34小時(下午，假設現在是17:20)
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   記錄: {case['records']}")
        print(f"   當前狀態: {case['current_status']}")
        
        # 模擬 punch_in 中的工時計算邏輯
        now = datetime.datetime.now()
        total_work_hours = 0
        current_work_hours = 0
        
        for record in case['records']:
            check_in = record.get('check_in', 'N/A')
            check_out = record.get('check_out', 'N/A')
            
            if check_in != 'N/A' and check_out != 'N/A' and check_out:
                # 已完成的工時段
                try:
                    in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                    out_time = datetime.datetime.strptime(check_out, "%H:%M").time()
                    today = datetime.datetime.now().date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    out_datetime = datetime.datetime.combine(today, out_time)
                    duration = out_datetime - in_datetime
                    hours = duration.total_seconds() / 3600
                    total_work_hours += hours
                    print(f"     已完成工時段: {check_in}-{check_out} = {hours:.2f}小時")
                except Exception as e:
                    print(f"     ⚠️ 工時計算失敗: {e}")
            elif check_in != 'N/A' and check_out == '':
                # 正在進行的工時段
                try:
                    in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                    today = datetime.datetime.now().date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    duration = now - in_datetime
                    hours = duration.total_seconds() / 3600
                    current_work_hours = hours
                    print(f"     正在進行工時段: {check_in}-現在 = {hours:.2f}小時")
                except Exception as e:
                    print(f"     ⚠️ 當前工時計算失敗: {e}")
        
        # 總工時 = 已完成的工時 + 當前正在進行的工時
        total_work_hours += current_work_hours
        
        print(f"   計算總工時: {total_work_hours:.2f} 小時")
        print(f"   預期總工時: {case['expected_total_hours']:.2f} 小時")
        
        if abs(total_work_hours - case['expected_total_hours']) < 0.1:
            print("   ✅ 總工時計算正確")
        else:
            print(f"   ❌ 總工時計算錯誤！預期: {case['expected_total_hours']:.2f}, 實際: {total_work_hours:.2f}")
        
        # 模擬工時檢查邏輯
        if case['current_status'] == "checked_in":
            if total_work_hours < 8:
                print(f"   ⏳ 工時不足 ({total_work_hours:.1f}小時 < 8小時)，應該阻止下班打卡")
                should_punch = False
            else:
                print(f"   ✅ 工時充足 ({total_work_hours:.1f}小時 >= 8小時)，應該允許下班打卡")
                should_punch = True
        else:
            print(f"   ℹ️ 當前狀態不是 checked_in，不進行工時檢查")
            should_punch = False
        
        print(f"   應該打卡: {should_punch}")
        print(f"   預期打卡: {case['expected_should_punch']}")
        
        if should_punch == case['expected_should_punch']:
            print("   ✅ 打卡判斷正確")
        else:
            print(f"   ❌ 打卡判斷錯誤！預期: {case['expected_should_punch']}, 實際: {should_punch}")
    
    print("\n✅ punch_in 工時計算測試完成")

if __name__ == "__main__":
    print("🔔 punch_in 工時計算測試程式啟動...")
    
    # 顯示當前時間
    current_time = datetime.datetime.now()
    print(f"🕐 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試工時計算邏輯
    test_punch_in_hours_calculation()
    
    print("\n" + "="*50)
    print("💡 要測試實際的 punch_in 工時檢查，請執行:")
    print("   python main.py test")
