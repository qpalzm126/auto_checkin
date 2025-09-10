#!/usr/bin/env python3
"""
測試 get_today_check_in 修復
"""
from web_automation import WebAutomation

def test_check_in_fix():
    """測試修復後的 get_today_check_in 方法"""
    print("🧪 開始測試修復後的 get_today_check_in 方法...")
    
    automation = WebAutomation()
    
    try:
        # 設置瀏覽器
        automation.setup_driver()
        
        # 登入
        if not automation.login():
            print("❌ 登入失敗，無法繼續測試")
            return
        
        print("✅ 登入成功，開始測試...")
        
        # 測試修復後的 get_today_check_in
        from attendance_parser import AttendanceParser
        check_in_time = AttendanceParser.get_today_check_in(automation.driver)
        print(f"🕘 get_today_check_in 結果: {check_in_time}")
        
        # 對比測試 get_today_attendance_records
        records = AttendanceParser.get_today_attendance_records(automation.driver)
        print(f"📊 get_today_attendance_records 結果: {len(records)} 筆記錄")
        
        if records:
            first_record = records[0]
            if first_record.get('check_in'):
                print(f"📝 第一筆記錄的 check_in: {first_record['check_in']}")
                
                # 比較兩個方法的結果
                from datetime import datetime
                today_date = datetime.now().date()
                first_check_in_time = datetime.strptime(first_record['check_in'], "%H:%M").time()
                first_check_in_datetime = datetime.combine(today_date, first_check_in_time)
                
                print(f"🔍 比較結果:")
                print(f"   get_today_check_in: {check_in_time}")
                print(f"   第一筆記錄時間: {first_check_in_datetime}")
                
                if check_in_time == first_check_in_datetime:
                    print("✅ 修復成功！兩個方法結果一致")
                else:
                    print("⚠️ 結果不一致，需要進一步調試")
            else:
                print("⚠️ 第一筆記錄沒有 check_in 時間")
        else:
            print("⚠️ 沒有找到打卡記錄")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if automation.driver:
            automation.driver.quit()
        print("✅ 測試完成")

if __name__ == "__main__":
    test_check_in_fix()
