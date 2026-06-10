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
                        r'\b(EST|CST|MST|PST|EDT|CDT|MDT|PDT|GMT|UTC|JST|KST|IST)\b',  # 特定時區縮寫
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
    def calculate_work_hours(records, include_in_progress=True):
        """計算總工時

        正確計算方式：將每筆 (check_out - check_in) 累加，這樣可以排除午休等
        非工作時段。若 include_in_progress=True 且最後一筆只有 check_in 沒有
        check_out（代表目前還在工作中），則把該段 (now - check_in) 也納入總工時。

        Args:
            records: 打卡記錄列表，每筆為 {'check_in': 'HH:MM', 'check_out': 'HH:MM' or ''}
            include_in_progress: 是否將進行中的工時段（尚未 check out 的最後一筆）納入總計

        Returns:
            float: 總工時（小時）
        """
        total_hours = 0

        # 與其他模組一致：GitHub Actions 環境內部時間為 UTC，需轉為台灣時間
        if os.getenv("GITHUB_ACTIONS"):
            now = datetime.datetime.now() + datetime.timedelta(hours=8)
        else:
            now = datetime.datetime.now()
        today = now.date()

        for record in records:
            try:
                check_in = record.get('check_in')
                check_out = record.get('check_out')

                if not check_in:
                    continue

                in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                in_datetime = datetime.datetime.combine(today, in_time)

                if check_out:
                    out_time = datetime.datetime.strptime(check_out, "%H:%M").time()
                    out_datetime = datetime.datetime.combine(today, out_time)
                    duration = out_datetime - in_datetime
                    total_hours += duration.total_seconds() / 3600
                elif include_in_progress:
                    # 尚未下班的進行中工時段
                    duration = now - in_datetime
                    if duration.total_seconds() > 0:
                        total_hours += duration.total_seconds() / 3600
            except Exception as e:
                print(f"⚠️ 計算工時時出錯: {e}")
                continue

        return total_hours
