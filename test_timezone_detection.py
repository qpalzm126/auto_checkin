#!/usr/bin/env python3
"""
測試時區檢測邏輯
驗證修正後的時區檢測是否正確識別打卡記錄
"""
import re

def test_timezone_detection():
    """測試時區檢測邏輯"""
    print("🧪 開始測試時區檢測邏輯...")
    
    # 測試案例
    test_cases = [
        {
            "name": "正常打卡記錄 - 應該不被誤判為時區行",
            "text": "Check in: 08:50 Check out: 12:00 Subtotal: 3:10",
            "expected": False
        },
        {
            "name": "正常打卡記錄 - 只有上班",
            "text": "Check in: 13:00 Check out: Subtotal:",
            "expected": False
        },
        {
            "name": "真正的時區行 - 應該被識別為時區行",
            "text": "Eastern Time Zone UTC-5",
            "expected": True
        },
        {
            "name": "時區縮寫 - 應該被識別為時區行",
            "text": "EST UTC+8 GMT",
            "expected": True
        },
        {
            "name": "包含 Check 但不是時區行",
            "text": "Check in: 09:00 Check out: 17:00",
            "expected": False
        },
        {
            "name": "包含 Subtotal 但不是時區行",
            "text": "Subtotal: 8:00 Total: 8:00",
            "expected": False
        }
    ]
    
    # 時區關鍵字列表
    timezone_keywords = [
        # 完整時區名稱
        'Eastern Time Zone', 'Central Time Zone', 'Mountain Time Zone', 
        'Pacific Time Zone', 'East Asia Time Zone', 'India Standard Time',
        'Greenwich Mean Time', 'Coordinated Universal Time',
        # 時區縮寫
        'EST', 'CST', 'MST', 'PST', 'EDT', 'CDT', 'MDT', 'PDT',
        'GMT', 'UTC', 'JST', 'KST', 'CST', 'IST',
        # UTC/GMT 偏移
        'UTC+', 'UTC-', 'GMT+', 'GMT-',
        # 地區名稱
        'Ann Arbor', 'Pittsburgh', 'Durham', 'Chicago', 'Texas', 'Colorado',
        'Washington', 'California', 'Taiwan', 'Singapore', 'Malaysia',
        'New York', 'Los Angeles', 'Seattle', 'Boston', 'Miami',
        'Asia/', 'America/', 'Europe/', 'Africa/', 'Australia/',
        # 其他可能的時區標識
        'Time Zone', 'Timezone', 'TZ', 'Offset'
    ]
    
    # 時區模式列表
    timezone_patterns = [
        r'UTC[+-]\d+',  # UTC+8, UTC-5
        r'GMT[+-]\d+',  # GMT+8, GMT-5
        r'\b(EST|CST|MST|PST|EDT|CDT|MDT|PDT|GMT|UTC|JST|KST|IST)\b',  # 特定時區縮寫
        r'[A-Z][a-z]+ Time Zone',  # Eastern Time Zone
        r'Asia/[A-Za-z_]+',  # Asia/Taipei
        r'America/[A-Za-z_]+',  # America/New_York
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {case['name']}")
        print(f"   文本: {case['text']}")
        
        # 檢查關鍵字匹配
        is_timezone_row = any(keyword in case['text'] for keyword in timezone_keywords)
        print(f"   關鍵字匹配: {is_timezone_row}")
        
        # 檢查模式匹配
        has_timezone_pattern = any(re.search(pattern, case['text'], re.IGNORECASE) for pattern in timezone_patterns)
        print(f"   模式匹配: {has_timezone_pattern}")
        
        # 綜合判斷
        is_timezone = is_timezone_row or has_timezone_pattern
        print(f"   判斷結果: {'時區行' if is_timezone else '正常行'}")
        print(f"   預期結果: {'時區行' if case['expected'] else '正常行'}")
        
        if is_timezone == case['expected']:
            print("   ✅ 判斷正確")
        else:
            print(f"   ❌ 判斷錯誤！預期: {case['expected']}, 實際: {is_timezone}")
    
    print("\n✅ 時區檢測邏輯測試完成")

if __name__ == "__main__":
    print("🔔 時區檢測測試程式啟動...")
    test_timezone_detection()
