"""
打卡記錄解析模組
處理從網頁解析打卡記錄和時間的功能
"""
import os
import re
import datetime
from selenium.webdriver.common.by import By

class AttendanceParser:
    """打卡記錄解析類別"""
    
    @staticmethod
    def get_today_check_in(driver):
        """獲取今日上班時間（備用方法）"""
        # 在 GitHub Actions 環境中，使用台灣時間來匹配打卡系統的日期
        if os.getenv("GITHUB_ACTIONS"):
            # 台灣時間 = UTC + 8 小時
            taiwan_time = datetime.datetime.now() + datetime.timedelta(hours=8)
            today_str = taiwan_time.strftime("%m/%d")
            print(f"🌏 使用台灣時間日期: {today_str}")
        else:
            today_str = datetime.datetime.now().strftime("%m/%d")
            print(f"🕐 使用本地時間日期: {today_str}")
        
        try:
            print(f"🔍 正在尋找今日上班時間，日期: {today_str}")
            
            # 使用與 get_today_attendance_records 相同的方法
            try:
                container = driver.find_element(By.XPATH, f"//div[contains(@class,'border') and contains(@class,'px-3') and .//div[contains(text(), '{today_str}')]]")
                print(f"✅ 找到日期容器")
            except Exception as e:
                print(f"❌ 找不到今日記錄: {e}")
                # 如果找不到今日記錄，使用預設時間
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                work_start = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 找不到今日記錄，備用方法使用預設上班時間: {work_start}")
                return work_start
            
            # 尋找所有打卡記錄行（排除標題行）
            rows = container.find_elements(By.XPATH, ".//div[contains(@class,'row') and contains(@class,'border-bottom') and contains(@class,'hover-bg-primary-light')]")
            print(f"📊 找到 {len(rows)} 個打卡記錄行")
            
            if not rows:
                print("⚠️ 沒有找到打卡記錄行")
                # 如果找不到記錄行，使用預設時間
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                work_start = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 沒有找到打卡記錄行，備用方法使用預設上班時間: {work_start}")
                return work_start
            
            # 處理第一行記錄（最早的打卡記錄）
            first_row = rows[0]
            try:
                print(f"🔍 解析第一行記錄...")
                
                # 獲取整行的文本
                row_text = first_row.text
                print(f"   行文本: {row_text}")
                
                # 檢查是否為時區相關行
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
                
                is_timezone_row = any(keyword in row_text for keyword in timezone_keywords)
                
                # 額外檢查：使用正則表達式檢測時區模式
                timezone_patterns = [
                    r'UTC[+-]\d+',  # UTC+8, UTC-5
                    r'GMT[+-]\d+',  # GMT+8, GMT-5
                    r'\b[A-Z]{3,4}\b',  # EST, CST, PST, JST
                    r'[A-Z][a-z]+ Time Zone',  # Eastern Time Zone
                    r'Asia/[A-Za-z_]+',  # Asia/Taipei
                    r'America/[A-Za-z_]+',  # America/New_York
                ]
                
                has_timezone_pattern = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in timezone_patterns)
                
                if is_timezone_row or has_timezone_pattern:
                    print(f"   ⚠️ 第一行是時區行，跳過")
                    print(f"      關鍵字匹配: {is_timezone_row}")
                    print(f"      模式匹配: {has_timezone_pattern}")
                    # 如果第一行是時區行，使用預設時間
                    today_date = datetime.datetime.now().date()
                    fallback_time = datetime.time(hour=9, minute=0)
                    work_start = datetime.datetime.combine(today_date, fallback_time)
                    print(f"⚠️ 第一行是時區行，備用方法使用預設上班時間: {work_start}")
                    return work_start
                
                # 使用正則表達式提取時間
                time_pattern = r'\b(\d{1,2}:\d{2})\b'
                times = re.findall(time_pattern, row_text)
                print(f"   找到時間: {times}")
                
                if times:
                    # 過濾掉可能的時區時間
                    valid_times = []
                    for time_str in times:
                        try:
                            hour, minute = map(int, time_str.split(':'))
                            # 排除明顯不是打卡時間的時間
                            # 打卡時間通常在 6:00-22:00 之間
                            if 6 <= hour <= 22:
                                valid_times.append(time_str)
                            else:
                                print(f"      ⚠️ 跳過可疑時間: {time_str} (不在正常打卡時間範圍)")
                        except ValueError:
                            print(f"      ⚠️ 跳過無效時間格式: {time_str}")
                    
                    if valid_times:
                        # 取第一個有效時間作為上班時間
                        time_str = valid_times[0]
                        today_date = datetime.datetime.now().date()
                        check_in_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                        work_start = datetime.datetime.combine(today_date, check_in_time)
                        print(f"🕘 備用方法偵測到今日上班時間: {work_start}")
                        return work_start
                    else:
                        print("⚠️ 沒有找到有效的打卡時間")
                else:
                    print("⚠️ 沒有找到時間格式")
                    
            except Exception as e:
                print(f"⚠️ 解析第一行記錄失敗: {e}")
                
        except Exception as e:
            print(f"❌ 讀取 Check in 失敗: {e}")
            import traceback
            traceback.print_exc()

        # 如果所有方法都失敗，就設為今天 09:00
        today_date = datetime.datetime.now().date()
        fallback_time = datetime.time(hour=9, minute=0)
        work_start = datetime.datetime.combine(today_date, fallback_time)
        print(f"⚠️ 備用方法使用預設上班時間: {work_start}")
        return work_start

    @staticmethod
    def get_today_attendance_records(driver):
        """獲取當天的完整打卡記錄"""
        # 在 GitHub Actions 環境中，使用台灣時間來匹配打卡系統的日期
        if os.getenv("GITHUB_ACTIONS"):
            # 台灣時間 = UTC + 8 小時
            taiwan_time = datetime.datetime.now() + datetime.timedelta(hours=8)
            today_str = taiwan_time.strftime("%m/%d")
            print(f"🌏 使用台灣時間日期: {today_str}")
        else:
            today_str = datetime.datetime.now().strftime("%m/%d")
            print(f"🕐 使用本地時間日期: {today_str}")
        
        records = []
        
        try:
            print(f"🔍 正在尋找日期: {today_str}")
            
            # 方法1: 尋找包含今日日期的 div
            # try:
            #     date_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{today_str}')]")
            #     print(f"✅ 找到日期 div: {date_div.text}")
                
            #     # 找到包含這個日期的容器
            #     container = date_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'border') and contains(@class,'px-3')]")
            #     print(f"✅ 找到日期容器")
                
            # except Exception as e:
            #     print(f"⚠️ 方法1失敗: {e}")
            #     # 方法2: 直接尋找包含日期的容器
            try:
                container = driver.find_element(By.XPATH, f"//div[contains(@class,'border') and contains(@class,'px-3') and .//div[contains(text(), '{today_str}')]]")
                print(f"✅ 方法2找到日期容器")
            except Exception as e2:
                print(f"❌ 方法2也失敗: {e2}")
                return []
            
            # 尋找所有打卡記錄行（排除標題行）
            rows = container.find_elements(By.XPATH, ".//div[contains(@class,'row') and contains(@class,'border-bottom') and contains(@class,'hover-bg-primary-light')]")
            print(f"📊 找到 {len(rows)} 個打卡記錄行")
            
            for i, row in enumerate(rows):
                try:
                    print(f"🔍 解析第 {i+1} 行...")
                    
                    # 獲取整行的文本
                    row_text = row.text
                    print(f"   行文本: {row_text}")
                    
                    # 檢查是否為時區相關行
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
                    
                    is_timezone_row = any(keyword in row_text for keyword in timezone_keywords)
                    
                    # 額外檢查：使用正則表達式檢測時區模式
                    timezone_patterns = [
                        r'UTC[+-]\d+',  # UTC+8, UTC-5
                        r'GMT[+-]\d+',  # GMT+8, GMT-5
                        r'\b[A-Z]{3,4}\b',  # EST, CST, PST, JST
                        r'[A-Z][a-z]+ Time Zone',  # Eastern Time Zone
                        r'Asia/[A-Za-z_]+',  # Asia/Taipei
                        r'America/[A-Za-z_]+',  # America/New_York
                    ]
                    
                    has_timezone_pattern = any(re.search(pattern, row_text, re.IGNORECASE) for pattern in timezone_patterns)
                    
                    if is_timezone_row or has_timezone_pattern:
                        print(f"   ⚠️ 第 {i+1} 行是時區行，跳過")
                        print(f"      關鍵字匹配: {is_timezone_row}")
                        print(f"      模式匹配: {has_timezone_pattern}")
                        continue
                    
                    # 使用正則表達式提取時間
                    time_pattern = r'\b(\d{1,2}:\d{2})\b'
                    times = re.findall(time_pattern, row_text)
                    print(f"   找到時間: {times}")
                    
                    if len(times) >= 1:
                        # 過濾掉可能的時區時間
                        valid_times = []
                        for time_str in times:
                            try:
                                hour, minute = map(int, time_str.split(':'))
                                # 排除明顯不是打卡時間的時間
                                # 打卡時間通常在 6:00-22:00 之間
                                if 6 <= hour <= 22:
                                    valid_times.append(time_str)
                                else:
                                    print(f"      ⚠️ 跳過可疑時間: {time_str} (不在正常打卡時間範圍)")
                            except ValueError:
                                print(f"      ⚠️ 跳過無效時間格式: {time_str}")
                        
                        if valid_times:
                            check_in_time = valid_times[0]
                            check_out_time = valid_times[1] if len(valid_times) > 1 else ""
                            
                            records.append({
                                'check_in': check_in_time,
                                'check_out': check_out_time
                            })
                            print(f"   ✅ 記錄 {i+1}: Check in={check_in_time}, Check out={check_out_time}")
                        else:
                            print(f"   ⚠️ 第 {i+1} 行沒有找到有效的打卡時間")
                    else:
                        print(f"   ⚠️ 第 {i+1} 行沒有找到時間")
                    
                except Exception as e:
                    print(f"   ❌ 解析第 {i+1} 行失敗: {e}")
                    continue
                    
            print(f"📋 當天打卡記錄: {records}")
            return records
            
        except Exception as e:
            print(f"❌ 讀取打卡記錄失敗: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_current_status(records):
        """判斷當前打卡狀態"""
        if not records:
            return "not_checked_in"
        
        print(f"🔍 分析打卡記錄以判斷當前狀態...")
        print(f"   記錄數量: {len(records)}")
        
        # 顯示所有記錄
        for i, record in enumerate(records):
            print(f"   記錄 {i+1}: check_in='{record['check_in']}', check_out='{record['check_out']}'")
        
        # 檢查最後一筆記錄的狀態
        last_record = records[-1]
        print(f"   最後一筆記錄: check_in='{last_record['check_in']}', check_out='{last_record['check_out']}'")
        
        # 判斷狀態邏輯
        if not last_record['check_in']:
            # 最後一筆記錄沒有上班時間
            status = "not_checked_in"
        elif not last_record['check_out']:
            # 最後一筆記錄有上班時間但沒有下班時間
            status = "checked_in"
        else:
            # 最後一筆記錄有完整的上班和下班時間
            status = "checked_out"
        
        print(f"   判斷結果: {status}")
        return status

    @staticmethod
    def calculate_work_hours(records):
        """計算總工時"""
        total_hours = 0
        
        for record in records:
            try:
                if record['check_in'] and record['check_out']:
                    in_time = datetime.datetime.strptime(record['check_in'], "%H:%M").time()
                    out_time = datetime.datetime.strptime(record['check_out'], "%H:%M").time()
                    today = datetime.datetime.now().date()
                    in_datetime = datetime.datetime.combine(today, in_time)
                    out_datetime = datetime.datetime.combine(today, out_time)
                    duration = out_datetime - in_datetime
                    hours = duration.total_seconds() / 3600
                    total_hours += hours
            except Exception as e:
                print(f"⚠️ 計算工時時出錯: {e}")
                continue
        
        return total_hours
