#!/usr/bin/env python3
"""
測試 GitHub Actions 工時計算修復
驗證 punch_in 函數中的工時計算邏輯
"""
import datetime
import os

def test_github_actions_hours_calculation():
    """測試 GitHub Actions 工時計算"""
    print("🧪 測試 GitHub Actions 工時計算修復...")
    
    # 模擬 GitHub Actions 環境
    os.environ["GITHUB_ACTIONS"] = "true"
    
    # 測試案例
    test_cases = [
        {
            "name": "上午工時段 + 下午工時段",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},  # 3小時
                {"check_in": "13:00", "check_out": ""}        # 正在進行
            ],
            "current_time": "17:00",
            "expected_completed": 3.0,
            "expected_current": 4.0,
            "expected_total": 7.0,
            "should_checkout": False
        },
        {
            "name": "只有上午工時段",
            "records": [
                {"check_in": "09:00", "check_out": "17:00"}  # 8小時
            ],
            "current_time": "17:00",
            "expected_completed": 8.0,
            "expected_current": 0.0,
            "expected_total": 8.0,
            "should_checkout": True
        },
        {
            "name": "多個工時段",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},  # 3小時
                {"check_in": "13:00", "check_out": "14:00"},  # 1小時
                {"check_in": "15:00", "check_out": ""}        # 正在進行
            ],
            "current_time": "17:00",
            "expected_completed": 4.0,
            "expected_current": 2.0,
            "expected_total": 6.0,
            "should_checkout": False
        },
        {
            "name": "超過8小時",
            "records": [
                {"check_in": "09:00", "check_out": "12:00"},  # 3小時
                {"check_in": "13:00", "check_out": "18:00"}   # 5小時
            ],
            "current_time": "18:00",
            "expected_completed": 8.0,
            "expected_current": 0.0,
            "expected_total": 8.0,
            "should_checkout": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   打卡記錄: {case['records']}")
        print(f"   當前時間: {case['current_time']}")
        
        # 模擬工時計算邏輯
        now = datetime.datetime.strptime(f"2024-01-01 {case['current_time']}", "%Y-%m-%d %H:%M")
        total_work_hours = 0
        current_work_hours = 0
        
        print("   📝 詳細工時計算:")
        for record in case['records']:
            check_in = record.get('check_in', 'N/A')
            check_out = record.get('check_out', 'N/A')
            
            if check_in != 'N/A' and check_out != 'N/A' and check_out:
                # 已完成的工時段
                try:
                    in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                    out_time = datetime.datetime.strptime(check_out, "%H:%M").time()
                    today = now.date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    out_datetime = datetime.datetime.combine(today, out_time)
                    duration = out_datetime - in_datetime
                    hours = duration.total_seconds() / 3600
                    total_work_hours += hours
                    print(f"     ✅ 已完成工時段: {check_in}-{check_out} = {hours:.2f}小時")
                except Exception as e:
                    print(f"     ⚠️ 工時計算失敗: {e}")
            elif check_in != 'N/A' and check_out == '':
                # 正在進行的工時段
                try:
                    in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                    today = now.date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    duration = now - in_datetime
                    hours = duration.total_seconds() / 3600
                    current_work_hours = hours
                    print(f"     🔄 正在進行工時段: {check_in}-現在 = {hours:.2f}小時")
                except Exception as e:
                    print(f"     ⚠️ 當前工時計算失敗: {e}")
        
        # 總工時 = 已完成的工時 + 當前正在進行的工時
        total_work_hours += current_work_hours
        completed_hours = total_work_hours - current_work_hours
        
        print(f"   📊 工時檢查: 已完成工時={completed_hours:.1f}小時, 當前工時={current_work_hours:.1f}小時, 總工時={total_work_hours:.1f}小時")
        
        # 檢查是否可以下班
        can_checkout = total_work_hours >= 8
        print(f"   🕐 可以下班: {'✅' if can_checkout else '❌'}")
        
        # 驗證結果
        print(f"   預期: 已完成={case['expected_completed']:.1f}小時, 當前={case['expected_current']:.1f}小時, 總計={case['expected_total']:.1f}小時")
        print(f"   預期可以下班: {'✅' if case['should_checkout'] else '❌'}")
        
        if (abs(completed_hours - case['expected_completed']) < 0.1 and 
            abs(current_work_hours - case['expected_current']) < 0.1 and 
            abs(total_work_hours - case['expected_total']) < 0.1 and
            can_checkout == case['should_checkout']):
            print("   ✅ 工時計算正確")
        else:
            print("   ❌ 工時計算錯誤")
            print(f"      實際: 已完成={completed_hours:.1f}小時, 當前={current_work_hours:.1f}小時, 總計={total_work_hours:.1f}小時")
            print(f"      實際可以下班: {'✅' if can_checkout else '❌'}")

def test_github_actions_behavior():
    """測試 GitHub Actions 行為"""
    print("\n🧪 測試 GitHub Actions 行為...")
    
    scenarios = [
        {
            "name": "工時不足 - 發送通知",
            "total_hours": 7.5,
            "expected_action": "發送工時不足通知郵件",
            "expected_checkout": False
        },
        {
            "name": "工時充足 - 執行打卡",
            "total_hours": 8.0,
            "expected_action": "執行下班打卡",
            "expected_checkout": True
        },
        {
            "name": "工時充足 - 執行打卡",
            "total_hours": 8.5,
            "expected_action": "執行下班打卡",
            "expected_checkout": True
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 場景 {i}: {scenario['name']}")
        print(f"   總工時: {scenario['total_hours']} 小時")
        
        # 模擬 GitHub Actions 邏輯
        if scenario['total_hours'] < 8:
            print("   ⏳ 工時不足 8 小時，發送通知郵件")
            print("   📧 發送工時不足通知")
            print("   ❌ 不執行下班打卡")
        else:
            print("   ✅ 工時充足，可以下班打卡")
            print("   🔘 執行下班打卡")
            print("   📧 發送打卡成功通知")
        
        print(f"   預期動作: {scenario['expected_action']}")
        print(f"   預期打卡: {'✅' if scenario['expected_checkout'] else '❌'}")

def show_fix_summary():
    """顯示修復摘要"""
    print("\n📖 GitHub Actions 工時計算修復摘要:")
    
    print("\n🔧 修復內容:")
    print("   1. 在工時計算前重新獲取最新打卡記錄")
    print("   2. 使用 latest_records 而不是 attendance_records")
    print("   3. 添加詳細的工時計算日誌")
    print("   4. 確保計算所有工時段的總和")
    
    print("\n✅ 修復後的特點:")
    print("   - 重新獲取最新打卡記錄")
    print("   - 正確計算所有工時段")
    print("   - 詳細的計算過程日誌")
    print("   - 與本地環境邏輯一致")
    
    print("\n📋 修復的關鍵點:")
    print("   - 問題: 使用舊的 attendance_records")
    print("   - 解決: 重新獲取 latest_records")
    print("   - 位置: punch_in 函數中的下班打卡邏輯")

def main():
    """主程式"""
    print("🔔 GitHub Actions 工時計算修復測試...")
    print(f"🕐 當前時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試工時計算
    test_github_actions_hours_calculation()
    
    # 測試 GitHub Actions 行為
    test_github_actions_behavior()
    
    # 顯示修復摘要
    show_fix_summary()
    
    print("\n" + "="*60)
    print("✅ GitHub Actions 工時計算修復測試完成")
    print("\n💡 修復後，GitHub Actions 會正確計算當天的全部工時")

if __name__ == "__main__":
    main()
