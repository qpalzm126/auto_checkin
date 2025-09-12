#!/usr/bin/env python3
"""
測試工時計算功能
驗證滿8小時工時的下班時間計算
"""
import datetime
from attendance_parser import AttendanceParser

def test_hours_calculation_logic():
    """測試工時計算邏輯"""
    print("🧪 開始測試工時計算邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "已下班 - 工時充足",
            "records": [
                {"check_in": "09:00", "check_out": "17:00"}
            ],
            "expected_status": "checked_out",
            "expected_total_hours": 8.0
        },
        {
            "name": "已下班 - 工時不足",
            "records": [
                {"check_in": "09:00", "check_out": "16:00"}
            ],
            "expected_status": "checked_out", 
            "expected_total_hours": 7.0
        },
        {
            "name": "正在上班 - 需要計算下班時間",
            "records": [
                {"check_in": "09:00", "check_out": ""}
            ],
            "expected_status": "checked_in",
            "expected_total_hours": 8.27  # 假設現在是 17:16，從 09:00 開始工作
        },
        {
            "name": "午休情況 - 需要計算下班時間",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},
                {"check_in": "13:00", "check_out": ""}
            ],
            "expected_status": "checked_in",
            "expected_total_hours": 7.27  # 3小時(上午) + 4.27小時(下午，假設現在是17:16)
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   記錄: {case['records']}")
        
        # 計算總工時（包括已完成的和正在進行的）
        total_hours = 0
        current_work_hours = 0
        now = datetime.datetime.now()
        
        for record in case['records']:
            if record.get('check_in') and record.get('check_out') and record['check_out']:
                # 已完成的工時段
                try:
                    in_time = datetime.datetime.strptime(record['check_in'], "%H:%M").time()
                    out_time = datetime.datetime.strptime(record['check_out'], "%H:%M").time()
                    today = datetime.datetime.now().date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    out_datetime = datetime.datetime.combine(today, out_time)
                    duration = out_datetime - in_datetime
                    hours = duration.total_seconds() / 3600
                    total_hours += hours
                except Exception as e:
                    print(f"    ⚠️ 工時計算失敗: {e}")
            elif record.get('check_in') and not record.get('check_out'):
                # 正在進行的工時段
                try:
                    in_time = datetime.datetime.strptime(record['check_in'], "%H:%M").time()
                    today = datetime.datetime.now().date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    duration = now - in_datetime
                    hours = duration.total_seconds() / 3600
                    current_work_hours = hours
                except Exception as e:
                    print(f"    ⚠️ 當前工時計算失敗: {e}")
        
        # 總工時 = 已完成的工時 + 當前正在進行的工時
        total_hours += current_work_hours
        
        print(f"   計算總工時: {total_hours:.2f} 小時")
        print(f"   預期總工時: {case['expected_total_hours']:.2f} 小時")
        
        if abs(total_hours - case['expected_total_hours']) < 0.01:
            print("   ✅ 總工時計算正確")
        else:
            print(f"   ❌ 總工時計算錯誤！預期: {case['expected_total_hours']:.2f}, 實際: {total_hours:.2f}")
        
        # 測試狀態判斷
        current_status = AttendanceParser.get_current_status(case['records'])
        print(f"   當前狀態: {current_status}")
        print(f"   預期狀態: {case['expected_status']}")
        
        if current_status == case['expected_status']:
            print("   ✅ 狀態判斷正確")
        else:
            print(f"   ❌ 狀態判斷錯誤！預期: {case['expected_status']}, 實際: {current_status}")
        
        # 計算下班時間（如果正在上班）
        if current_status == "checked_in":
            remaining_hours = 8 - total_hours
            print(f"   還需要工時: {remaining_hours:.2f} 小時")
            
            if remaining_hours > 0:
                # 找到最後一次上班時間
                last_checkin = None
                for record in reversed(case['records']):
                    if record.get('check_in') and not record.get('check_out'):
                        last_checkin = record['check_in']
                        break
                
                if last_checkin:
                    try:
                        check_in_time = datetime.datetime.strptime(last_checkin, "%H:%M").time()
                        today = datetime.datetime.now().date()
                        work_start = datetime.datetime.combine(today, check_in_time)
                        checkout_time = work_start + datetime.timedelta(hours=8)
                        print(f"   最後上班時間: {last_checkin}")
                        print(f"   滿8小時下班時間: {checkout_time.strftime('%H:%M')}")
                        
                        # 計算還需要多少時間
                        now = datetime.datetime.now()
                        time_remaining = checkout_time - now
                        if time_remaining.total_seconds() > 0:
                            remaining_minutes = int(time_remaining.total_seconds() / 60)
                            print(f"   還需要工作: {remaining_minutes} 分鐘")
                        else:
                            print("   🎉 已經可以下班了！")
                    except Exception as e:
                        print(f"   ⚠️ 下班時間計算失敗: {e}")
            else:
                print("   🎉 已經滿8小時了！可以下班了！")
    
    print("\n✅ 工時計算邏輯測試完成")

if __name__ == "__main__":
    print("🔔 工時計算測試程式啟動...")
    
    # 顯示當前時間
    current_time = datetime.datetime.now()
    print(f"🕐 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試工時計算邏輯
    test_hours_calculation_logic()
    
    print("\n" + "="*50)
    print("💡 要測試實際的工時計算，請執行:")
    print("   python main.py hours")
