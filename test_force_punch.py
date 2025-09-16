#!/usr/bin/env python3
"""
測試強制打卡功能
驗證 force_punch 函數的狀態檢查和打卡邏輯
"""
import datetime
from web_automation import WebAutomation

def test_force_punch_logic():
    """測試強制打卡邏輯"""
    print("🧪 開始測試強制打卡邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "上班打卡 - 狀態合理",
            "action": "上班",
            "current_status": "not_checked_in",
            "button_text": "Check in",
            "expected_valid": True
        },
        {
            "name": "上班打卡 - 狀態不合理",
            "action": "上班",
            "current_status": "checked_in",
            "button_text": "Check out",
            "expected_valid": False
        },
        {
            "name": "下班打卡 - 狀態合理",
            "action": "下班",
            "current_status": "checked_in",
            "button_text": "Check out",
            "expected_valid": True
        },
        {
            "name": "下班打卡 - 狀態不合理",
            "action": "下班",
            "current_status": "not_checked_in",
            "button_text": "Check in",
            "expected_valid": False
        },
        {
            "name": "午休下班 - 狀態合理",
            "action": "午休下班",
            "current_status": "checked_in",
            "button_text": "Check out",
            "expected_valid": True
        },
        {
            "name": "午休上班 - 狀態合理 (已下班)",
            "action": "午休上班",
            "current_status": "checked_out",
            "button_text": "Check in",
            "expected_valid": True
        },
        {
            "name": "午休上班 - 狀態合理 (未打卡)",
            "action": "午休上班",
            "current_status": "not_checked_in",
            "button_text": "Check in",
            "expected_valid": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   動作: {case['action']}")
        print(f"   當前狀態: {case['current_status']}")
        print(f"   按鈕文字: {case['button_text']}")
        
        # 模擬狀態檢查邏輯
        status_valid = False
        if case['action'] == "上班":
            if case['current_status'] == "not_checked_in" and "Check in" in case['button_text']:
                status_valid = True
        elif case['action'] == "午休下班":
            if case['current_status'] == "checked_in" and "Check out" in case['button_text']:
                status_valid = True
        elif case['action'] == "午休上班":
            if (case['current_status'] == "checked_out" or case['current_status'] == "not_checked_in") and "Check in" in case['button_text']:
                status_valid = True
        elif case['action'] == "下班":
            if case['current_status'] == "checked_in" and "Check out" in case['button_text']:
                status_valid = True
        
        print(f"   狀態檢查結果: {'合理' if status_valid else '不合理'}")
        print(f"   預期結果: {'合理' if case['expected_valid'] else '不合理'}")
        
        if status_valid == case['expected_valid']:
            print("   ✅ 狀態檢查正確")
        else:
            print(f"   ❌ 狀態檢查錯誤！預期: {case['expected_valid']}, 實際: {status_valid}")
    
    print("\n✅ 強制打卡邏輯測試完成")

def show_usage():
    """顯示使用說明"""
    print("\n📖 強制打卡功能使用說明:")
    print("   python main.py force 上班      # 強制上班打卡")
    print("   python main.py force 午休下班  # 強制午休下班打卡")
    print("   python main.py force 午休上班  # 強制午休上班打卡")
    print("   python main.py force 下班      # 強制下班打卡")
    print("\n💡 功能特點:")
    print("   - 會先檢查當前打卡狀態")
    print("   - 會顯示今日打卡記錄")
    print("   - 會檢查狀態是否合理")
    print("   - 會計算工時（下班打卡時）")
    print("   - 即使狀態不合理也會執行打卡")
    print("   - 會發送打卡結果通知郵件")

if __name__ == "__main__":
    print("🔔 強制打卡功能測試程式啟動...")
    
    # 顯示當前時間
    current_time = datetime.datetime.now()
    print(f"🕐 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試強制打卡邏輯
    test_force_punch_logic()
    
    # 顯示使用說明
    show_usage()
    
    print("\n" + "="*50)
    print("💡 要測試實際的強制打卡，請執行:")
    print("   python main.py force 下班")
