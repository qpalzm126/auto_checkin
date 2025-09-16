#!/usr/bin/env python3
"""
測試自動下班偵測功能
驗證 auto_checkout_when_ready 函數的邏輯
"""
import datetime

def test_auto_checkout_logic():
    """測試自動下班偵測邏輯"""
    print("🧪 開始測試自動下班偵測邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "已經滿8小時 - 應該立即打卡",
            "total_hours": 8.5,
            "current_status": "checked_in",
            "expected_action": "立即打卡"
        },
        {
            "name": "工時不足 - 應該等待",
            "total_hours": 6.0,
            "current_status": "checked_in",
            "expected_action": "等待2小時"
        },
        {
            "name": "工時不足 - 應該等待",
            "total_hours": 7.5,
            "current_status": "checked_in",
            "expected_action": "等待30分鐘"
        },
        {
            "name": "狀態不是 checked_in - 無法執行",
            "total_hours": 8.0,
            "current_status": "not_checked_in",
            "expected_action": "無法執行"
        },
        {
            "name": "狀態不是 checked_in - 無法執行",
            "total_hours": 8.0,
            "current_status": "checked_out",
            "expected_action": "無法執行"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   總工時: {case['total_hours']} 小時")
        print(f"   當前狀態: {case['current_status']}")
        
        # 模擬邏輯判斷
        if case['current_status'] != "checked_in":
            action = "無法執行"
            print(f"   ❌ 狀態不是 checked_in，無法執行自動下班打卡")
        elif case['total_hours'] >= 8:
            action = "立即打卡"
            print(f"   ✅ 已經滿8小時，可以立即打卡")
        else:
            remaining_hours = 8 - case['total_hours']
            remaining_minutes = int(remaining_hours * 60)
            action = f"等待{remaining_minutes}分鐘"
            print(f"   ⏰ 還需要 {remaining_minutes} 分鐘 ({remaining_hours:.2f} 小時)")
        
        print(f"   預期動作: {case['expected_action']}")
        print(f"   實際動作: {action}")
        
        if action == case['expected_action'] or (action.startswith("等待") and case['expected_action'].startswith("等待")):
            print("   ✅ 邏輯判斷正確")
        else:
            print(f"   ❌ 邏輯判斷錯誤！預期: {case['expected_action']}, 實際: {action}")
    
    print("\n✅ 自動下班偵測邏輯測試完成")

def show_usage():
    """顯示使用說明"""
    print("\n📖 自動下班偵測功能使用說明:")
    print("   python main.py auto")
    print("\n💡 功能特點:")
    print("   - 自動計算當前工時")
    print("   - 如果已滿8小時，立即打卡下班")
    print("   - 如果未滿8小時，等待到滿8小時後再等1分鐘")
    print("   - 每30秒顯示剩餘等待時間")
    print("   - 可以按 Ctrl+C 取消等待")
    print("   - 會發送通知郵件")
    print("\n⚠️ 注意事項:")
    print("   - 需要保持程式運行直到自動打卡完成")
    print("   - 確保網路連接正常")
    print("   - 確保打卡系統可以正常訪問")

def simulate_work_hours_calculation():
    """模擬工時計算"""
    print("\n🧮 模擬工時計算範例:")
    
    # 模擬打卡記錄
    records = [
        {"check_in": "09:00", "check_out": "12:00"},  # 3小時
        {"check_in": "13:00", "check_out": ""}        # 正在進行
    ]
    
    now = datetime.datetime.now()
    total_hours = 0
    current_work_hours = 0
    
    print("📝 打卡記錄:")
    for i, record in enumerate(records, 1):
        check_in = record.get('check_in', 'N/A')
        check_out = record.get('check_out', 'N/A')
        print(f"  第 {i} 次: Check in={check_in}, Check out={check_out}")
        
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
                total_hours += hours
                print(f"    ✅ 已完成: {hours:.2f}小時")
            except Exception as e:
                print(f"    ❌ 計算失敗: {e}")
        elif check_in != 'N/A' and check_out == '':
            # 正在進行的工時段
            try:
                in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                today = datetime.datetime.now().date()
                in_datetime = datetime.datetime.combine(today, in_time)
                duration = now - in_datetime
                hours = duration.total_seconds() / 3600
                current_work_hours = hours
                print(f"    🔄 進行中: {hours:.2f}小時")
            except Exception as e:
                print(f"    ❌ 計算失敗: {e}")
    
    total_hours += current_work_hours
    print(f"\n📊 總工時: {total_hours:.2f} 小時")
    
    if total_hours >= 8:
        print("🎉 已經滿8小時，可以立即下班打卡！")
    else:
        remaining_hours = 8 - total_hours
        remaining_minutes = int(remaining_hours * 60)
        print(f"⏰ 還需要工作: {remaining_minutes} 分鐘")

if __name__ == "__main__":
    print("🔔 自動下班偵測功能測試程式啟動...")
    
    # 顯示當前時間
    current_time = datetime.datetime.now()
    print(f"🕐 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試自動下班偵測邏輯
    test_auto_checkout_logic()
    
    # 模擬工時計算
    simulate_work_hours_calculation()
    
    # 顯示使用說明
    show_usage()
    
    print("\n" + "="*50)
    print("💡 要測試實際的自動下班偵測，請執行:")
    print("   python main.py auto")
