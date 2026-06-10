"""
網頁自動化模組
處理瀏覽器操作和網頁互動功能
"""
import os
import time
import datetime
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from config import Config
from attendance_parser import AttendanceParser
from email_service import EmailService
from telegram_service import TelegramService

class WebAutomation:
    """網頁自動化類別"""
    
    def __init__(self):
        self.driver = None
        self.work_start_time = None
        self.today_log = []
    
    def setup_driver(self):
        """設置 Chrome 瀏覽器"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 使用 webdriver-manager 自動下載和管理 ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def login(self, max_retries=2):
        """登入系統，支援重試機制"""
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 第 {attempt + 1} 次登入嘗試...")
                    time.sleep(5)  # 重試前等待5秒
                else:
                    print("🌐 正在連接網站...")
                
                self.driver.get(Config.LOGIN_URL)
                
                print("🔐 正在登入...")
                self.driver.find_element(By.ID, "__BVID__6").send_keys(Config.USERNAME)
                self.driver.find_element(By.ID, "__BVID__8").send_keys(Config.PASSWORD)
                self.driver.find_element(By.XPATH, "//button[contains(text(),'Log In')]").click()
                time.sleep(3)
                
                # 檢查是否登入成功 - 檢查頁面是否包含打卡相關元素
                try:
                    # 檢查是否有打卡按鈕或相關元素
                    check_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check')]")
                    if check_buttons:
                        if attempt > 0:
                            print(f"✅ 登入成功 - 第 {attempt + 1} 次嘗試成功，找到打卡按鈕")
                        else:
                            print("✅ 登入成功 - 找到打卡按鈕")
                        return True
                    
                    print(f"❌ 登入失敗 - 第 {attempt + 1} 次嘗試，未找到登入成功指標")
                    
                    # 如果不是最後一次嘗試，繼續重試
                    if attempt < max_retries:
                        print(f"⏳ 等待5秒後重試...")
                        continue
                    else:
                        print("❌ 所有登入嘗試都失敗了")
                        return False
                    
                except Exception as e:
                    print(f"❌ 檢查登入狀態時出錯: {e}")
                    if attempt < max_retries:
                        print(f"⏳ 等待5秒後重試...")
                        continue
                    else:
                        return False
                    
            except Exception as e:
                print(f"❌ 登入過程出錯: {e}")
                if attempt < max_retries:
                    print(f"⏳ 等待5秒後重試...")
                    continue
                else:
                    return False
        
        return False
    
    def punch_in(self, label=""):
        """執行打卡動作"""
        if not Config.AUTO_CHECKIN_ENABLED:
            print("⏸ 已停用自動打卡 (AUTO_CHECKIN_ENABLED=false)")
            return

        if Config.is_skip_today():
            return

        today = datetime.datetime.today().weekday()
        if today not in Config.WORK_DAYS:
            print(f"⏸ 今天不是工作日，跳過 {label}")
            return

        # 獲取當天的打卡記錄來判斷當前狀態
        attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
        
        # 優先使用當天第一筆打卡記錄的 Check in 時間作為上班時間
        if attendance_records:
            first_record = attendance_records[0]
            if first_record.get('check_in'):
                try:
                    check_in_time_str = first_record['check_in']
                    today_date = datetime.datetime.now().date()
                    check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
                    self.work_start_time = datetime.datetime.combine(today_date, check_in_time)
                    
                    # 檢查是否在 GitHub Actions 環境中
                    if os.getenv("GITHUB_ACTIONS"):
                        print(f"🕘 使用當天第一筆打卡記錄作為上班時間 (台灣時間): {self.work_start_time}")
                        print(f"ℹ️ 打卡系統顯示台灣時間，工時計算將基於台灣時間")
                    else:
                        print(f"🕘 使用當天第一筆打卡記錄作為上班時間: {self.work_start_time}")
                except Exception as e:
                    print(f"⚠️ 解析第一筆打卡時間失敗: {e}")
                    # 如果解析失敗，設為預設時間
                    if not self.work_start_time:
                        today_date = datetime.datetime.now().date()
                        fallback_time = datetime.time(hour=9, minute=0)
                        self.work_start_time = datetime.datetime.combine(today_date, fallback_time)
                        print(f"⚠️ 使用預設上班時間: {self.work_start_time}")
        else:
            # 如果沒有打卡記錄，設為預設時間
            if not self.work_start_time:
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                self.work_start_time = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 沒有打卡記錄，使用預設上班時間: {self.work_start_time}")
        
        # 調試信息：顯示當前上班時間
        if self.work_start_time:
            print(f"🔍 當前設定的上班時間: {self.work_start_time}")
        else:
            print("⚠️ 警告：無法獲取上班時間，工時檢查將被跳過")
        
        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
        if not buttons:
            log_entry = f"{label}: 找不到打卡按鈕"
            self.today_log.append(log_entry)
            EmailService.send_checkin_notification(
                "找不到打卡按鈕", 
                label, 
                source="系統檢查",
                attendance_records=attendance_records
            )
            self.driver.quit()
            return

        btn = buttons[0]
        btn_text = btn.text.strip()
        
        # 根據打卡記錄判斷當前狀態
        current_status = AttendanceParser.get_current_status(attendance_records)

        try:
            # 智能判斷打卡邏輯
            should_punch = False
            
            if label == "上班":
                if current_status == "not_checked_in" and "Check in" in btn_text:
                    should_punch = True
                    result = "上班打卡成功"
                else:
                    result = f"上班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
                    
            elif label == "午休下班":
                if current_status == "checked_in" and "Check out" in btn_text:
                    should_punch = True
                    result = "午休下班打卡成功"
                else:
                    result = f"午休下班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
                    
            elif label == "午休上班":
                if (current_status == "checked_out" or current_status == "not_checked_in") and "Check in" in btn_text:
                    should_punch = True
                    result = "午休上班打卡成功"
                else:
                    result = f"午休上班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
                    
            elif label == "下班":
                if current_status == "checked_in" and "Check out" in btn_text:
                    # 檢查工時 - 使用 calculate_work_hours 函數
                    print("🔄 使用 calculate_work_hours 函數計算工時...")
                    
                    # 調用 calculate_work_hours 函數來計算工時
                    work_hours_result = self._calculate_work_hours_for_punch()
                    
                    if work_hours_result is None:
                        print("❌ 工時計算失敗，無法執行下班打卡")
                        return
                    
                    total_work_hours, current_work_hours = work_hours_result
                    
                    if total_work_hours < 8:
                        # 在 GitHub Actions 環境中，發送郵件通知而不是延後
                        if os.getenv("GITHUB_ACTIONS"):
                            print(f"⏳ 工時不足 8 小時 (目前: {total_work_hours:.1f} 小時)，發送通知郵件")
                            remaining_hours = 8 - total_work_hours
                            remaining_minutes = int(remaining_hours * 60)
                            
                            # 發送工時不足通知
                            EmailService.send_checkin_notification(
                                f"工時不足 ({total_work_hours:.1f}小時)，需要再工作 {remaining_minutes} 分鐘", 
                                "下班打卡 - 工時不足", 
                                work_hours=total_work_hours,
                                source="GitHub Actions 工時檢查",
                                attendance_records=attendance_records
                            )
                            result = f"工時不足 ({total_work_hours:.1f}小時)，已發送通知郵件"
                            self.driver.quit()
                            return
                        else:
                            # 本地環境：延後打卡
                            delay_minutes = int((8 - total_work_hours) * 60) + 1
                            now = datetime.datetime.now()
                            new_time = now + datetime.timedelta(minutes=delay_minutes)
                            print(f"⏳ 未滿 8 小時，延後到 {new_time.strftime('%H:%M')} 下班打卡")
                            schedule.every().day.at(new_time.strftime("%H:%M")).do(self.punch_in, label="下班")
                            self.driver.quit()
                            return
                    else:
                        print(f"✅ 工時充足 ({total_work_hours:.1f}小時)，可以下班打卡")
                    
                    should_punch = True
                    result = "下班打卡成功"
                else:
                    result = f"下班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
            
            # 執行打卡
            if should_punch:
                btn.click()
                if label == "上班":
                    self.work_start_time = datetime.datetime.now()
            else:
                print(f"⏸ {result}")
                
        except Exception as e:
            result = f"{label} 失敗: {e}"

        # 更新 log
        # 從已獲取的打卡記錄中獲取上班時間
        check_in_time = "N/A"
        if attendance_records and attendance_records[0].get('check_in'):
            check_in_time = attendance_records[0]['check_in']
        log_entry = f"{label}: {result}, Check in: {check_in_time}, Check out: 未抓取"
        self.today_log.append(log_entry)

        # 寄信通知
        EmailService.send_checkin_notification(
            result, 
            label, 
            source="打卡系統",
            attendance_records=attendance_records
        )
        
        # Telegram 通知
        check_out_time = "N/A"
        if attendance_records and attendance_records[0].get('check_out'):
            check_out_time = attendance_records[0]['check_out']
        TelegramService.send_checkin_notification(
            result,
            label,
            source="打卡系統",
            check_in_time=check_in_time,
            check_out_time=check_out_time,
        )

        print(f"📌 {label} 完成: {result}")
        self.driver.quit()
    
    def test_attendance_records(self):
        """測試打卡記錄解析功能"""
        try:
            print("🧪 開始測試打卡記錄解析...")
            
            # 設置瀏覽器
            self.setup_driver()
            
            # 登入
            if not self.login():
                return
            
            print("📋 正在解析打卡記錄...")
            
            # 先檢查頁面內容
            print("🔍 檢查頁面內容...")
            page_source = self.driver.page_source
            
            # 測試完整打卡記錄
            records = AttendanceParser.get_today_attendance_records(self.driver)
            print(f"📊 打卡記錄數量: {len(records)}")
            
            # 測試上班時間解析（使用新的優先邏輯）
            work_start = None
            if records:
                first_record = records[0]
                if first_record.get('check_in'):
                    try:
                        check_in_time_str = first_record['check_in']
                        today_date = datetime.datetime.now().date()
                        check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
                        work_start = datetime.datetime.combine(today_date, check_in_time)
                        
                        # 檢查是否在 GitHub Actions 環境中
                        if os.getenv("GITHUB_ACTIONS"):
                            print(f"🕘 使用當天第一筆打卡記錄作為上班時間 (台灣時間): {work_start}")
                            print(f"ℹ️ 打卡系統顯示台灣時間，工時計算將基於台灣時間")
                        else:
                            print(f"🕘 使用當天第一筆打卡記錄作為上班時間: {work_start}")
                    except Exception as e:
                        print(f"⚠️ 解析第一筆打卡時間失敗: {e}")
                        # 使用預設時間
                        today_date = datetime.datetime.now().date()
                        fallback_time = datetime.time(hour=9, minute=0)
                        work_start = datetime.datetime.combine(today_date, fallback_time)
                        print(f"⚠️ 使用預設上班時間: {work_start}")
            else:
                # 沒有打卡記錄，使用預設時間
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                work_start = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 沒有打卡記錄，使用預設上班時間: {work_start}")
            
            print(f"🕘 最終上班時間: {work_start}")
            
            if records:
                print("📝 詳細打卡記錄:")
                for i, record in enumerate(records, 1):
                    check_in = record.get('check_in', 'N/A')
                    check_out = record.get('check_out', 'N/A')
                    print(f"  第 {i} 次:")
                    print(f"    Check in:  {check_in}")
                    print(f"    Check out: {check_out}")
                    
                    # 計算工時
                    if check_in != 'N/A' and check_out != 'N/A' and check_out:
                        try:
                            in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                            out_time = datetime.datetime.strptime(check_out, "%H:%M").time()
                            today = datetime.datetime.now().date()
                            in_datetime = datetime.datetime.combine(today, in_time)
                            out_datetime = datetime.datetime.combine(today, out_time)
                            duration = out_datetime - in_datetime
                            hours = duration.total_seconds() / 3600
                            print(f"    工時: {hours:.2f} 小時")
                        except Exception as e:
                            print(f"    工時計算失敗: {e}")
                    else:
                        print(f"    工時: 進行中...")
            else:
                print("❌ 沒有找到打卡記錄")
            
            # 測試 current_status 判斷
            print("\n🔍 測試 current_status 判斷...")
            current_status = AttendanceParser.get_current_status(records)
            print(f"📊 解析出的 current_status: {current_status}")
            
            # 驗證 current_status 的邏輯
            if records:
                last_record = records[-1]
                print(f"📝 最後一筆記錄: check_in='{last_record.get('check_in', 'N/A')}', check_out='{last_record.get('check_out', 'N/A')}'")
                
                # 手動驗證狀態判斷邏輯
                expected_status = None
                if not last_record.get('check_in'):
                    expected_status = "not_checked_in"
                elif not last_record.get('check_out'):
                    expected_status = "checked_in"
                else:
                    expected_status = "checked_out"
                
                print(f"🎯 預期狀態: {expected_status}")
                
                if current_status == expected_status:
                    print("✅ current_status 判斷正確")
                else:
                    print(f"❌ current_status 判斷錯誤！預期: {expected_status}, 實際: {current_status}")
            else:
                print("ℹ️ 沒有打卡記錄，current_status 應該為 'not_checked_in'")
                if current_status == "not_checked_in":
                    print("✅ current_status 判斷正確")
                else:
                    print(f"❌ current_status 判斷錯誤！預期: not_checked_in, 實際: {current_status}")
                
            # 測試按鈕狀態
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
            if buttons:
                print(f"🔘 找到 {len(buttons)} 個打卡按鈕:")
                for i, btn in enumerate(buttons, 1):
                    print(f"  按鈕 {i}: {btn.text.strip()}")
                
                # 檢查按鈕狀態與 current_status 的一致性
                print("\n🔍 檢查按鈕狀態與 current_status 的一致性...")
                if buttons:
                    btn_text = buttons[0].text.strip()
                    print(f"📱 按鈕文字: '{btn_text}'")
                    print(f"📊 current_status: '{current_status}'")
                    
                    # 驗證邏輯一致性
                    is_consistent = False
                    if current_status == "not_checked_in" and "Check in" in btn_text:
                        is_consistent = True
                        print("✅ 狀態一致: 未打卡 → 顯示 Check in 按鈕")
                    elif current_status == "checked_in" and "Check out" in btn_text:
                        is_consistent = True
                        print("✅ 狀態一致: 已上班 → 顯示 Check out 按鈕")
                    elif current_status == "checked_out" and "Check in" in btn_text:
                        is_consistent = True
                        print("✅ 狀態一致: 已下班 → 顯示 Check in 按鈕")
                    else:
                        print(f"❌ 狀態不一致: current_status='{current_status}' 但按鈕顯示 '{btn_text}'")
                        print("💡 這可能表示:")
                        print("   - 打卡記錄解析有問題")
                        print("   - 按鈕狀態檢測有問題")
                        print("   - 網頁狀態與記錄不同步")
            else:
                print("❌ 沒有找到打卡按鈕")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
            print("✅ 測試完成")
    
    def debug_html_structure(self):
        """調試 HTML 結構"""
        try:
            print("🔍 開始調試 HTML 結構...")
            
            # 設置瀏覽器
            self.setup_driver()
            
            # 登入
            if not self.login():
                return
            
            print("🔍 檢查頁面結構...")
            
            # 檢查所有包含日期的 div
            date_divs = self.driver.find_elements(By.XPATH, "//div[contains(text(), '/')]")
            print(f"📅 找到 {len(date_divs)} 個包含日期的 div:")
            for i, div in enumerate(date_divs[:10]):  # 只顯示前10個
                print(f"  {i+1}: {div.text}")
            
            # 檢查所有包含時間的文本（排除時區）
            import re
            page_text = self.driver.page_source
            
            # 排除時區相關的文本
            timezone_keywords = ['Eastern Time Zone', 'Central Time Zone', 'Mountain Time Zone', 
                               'Pacific Time Zone', 'East Asia Time Zone', 'India Standard Time',
                               'Ann Arbor', 'Pittsburgh', 'Durham', 'Chicago', 'Texas', 'Colorado',
                               'Washington', 'California', 'Taiwan', 'Singapore', 'Malaysia']
            
            # 檢查是否包含時區關鍵字
            is_timezone_section = any(keyword in page_text for keyword in timezone_keywords)
            if is_timezone_section:
                print("⚠️ 頁面包含時區區域")
            
            time_pattern = r'\b(\d{1,2}:\d{2})\b'
            times = re.findall(time_pattern, page_text)
            print(f"🕐 頁面中找到的所有時間: {times}")
            
            # 檢查容器結構
            containers = self.driver.find_elements(By.XPATH, "//div[contains(@class,'border') and contains(@class,'px-3')]")
            print(f"📦 找到 {len(containers)} 個邊框容器:")
            for i, container in enumerate(containers):
                print(f"  容器 {i+1}: {container.get_attribute('class')}")
                print(f"    文本: {container.text[:100]}...")
            
        except Exception as e:
            print(f"❌ 調試失敗: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
            print("✅ 調試完成")
    
    def _calculate_work_hours_for_punch(self):
        """為打卡計算工時，返回 (total_work_hours, current_work_hours) 或 None"""
        try:
            print("🧮 開始計算工時...")
            
            # 獲取當天的打卡記錄
            attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
            print(f"📊 打卡記錄數量: {len(attendance_records)}")
            
            if not attendance_records:
                print("❌ 沒有找到今天的打卡記錄")
                return None
            
            # 計算工時 - 使用與 calculate_work_hours 完全相同的邏輯
            total_work_hours = 0
            current_work_hours = 0  # 當前正在進行的工時
            
            # 在 GitHub Actions 環境中使用台灣時間
            if os.getenv("GITHUB_ACTIONS"):
                # GitHub Actions 使用 UTC 時間，台灣時間 = UTC + 8
                now = datetime.datetime.now() + datetime.timedelta(hours=8)
                print(f"🕐 當前時間 (台灣時間): {now.strftime('%H:%M:%S')}")
            else:
                now = datetime.datetime.now()
                print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
            
            for i, record in enumerate(attendance_records, 1):
                check_in = record.get('check_in', 'N/A')
                check_out = record.get('check_out', 'N/A')
                
                print(f"  第 {i} 次:")
                print(f"    Check in:  {check_in}")
                print(f"    Check out: {check_out}")
                
                # 計算這段的工時
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
                        print(f"    工時: {hours:.2f} 小時 (已完成)")
                    except Exception as e:
                        print(f"    工時計算失敗: {e}")
                elif check_in != 'N/A' and check_out == '':
                    # 正在進行的工時段
                    try:
                        in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                        today = datetime.datetime.now().date()
                        in_datetime = datetime.datetime.combine(today, in_time)
                        duration = now - in_datetime
                        hours = duration.total_seconds() / 3600
                        current_work_hours = hours
                        print(f"    工時: {hours:.2f} 小時 (進行中)")
                    except Exception as e:
                        print(f"    當前工時計算失敗: {e}")
                        current_work_hours = 0
            
            # 總工時 = 已完成的工時 + 當前正在進行的工時
            total_work_hours += current_work_hours
            
            print(f"\n📊 已完成工時: {total_work_hours - current_work_hours:.2f} 小時")
            print(f"📊 當前工時: {current_work_hours:.2f} 小時")
            print(f"📊 總工時: {total_work_hours:.2f} 小時")
            
            return (total_work_hours, current_work_hours)
            
        except Exception as e:
            print(f"❌ 計算工時失敗: {e}")
            return None

    def calculate_work_hours(self):
        """計算今天滿8小時工時需要什麼時候下班"""
        try:
            print("🧮 開始計算工時...")
            
            # 獲取當天的打卡記錄
            attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
            print(f"📊 打卡記錄數量: {len(attendance_records)}")
            
            if not attendance_records:
                print("❌ 沒有找到今天的打卡記錄")
                return
            
            # 顯示所有打卡記錄
            print("\n📝 今天的打卡記錄:")
            total_work_hours = 0
            current_work_hours = 0  # 當前正在進行的工時
            
            # 在 GitHub Actions 環境中使用台灣時間
            if os.getenv("GITHUB_ACTIONS"):
                # GitHub Actions 使用 UTC 時間，台灣時間 = UTC + 8
                now = datetime.datetime.now() + datetime.timedelta(hours=8)
                print(f"🕐 當前時間 (台灣時間): {now.strftime('%H:%M:%S')}")
            else:
                now = datetime.datetime.now()
                print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
            
            for i, record in enumerate(attendance_records, 1):
                check_in = record.get('check_in', 'N/A')
                check_out = record.get('check_out', 'N/A')
                print(f"  第 {i} 次:")
                print(f"    Check in:  {check_in}")
                print(f"    Check out: {check_out}")
                
                # 計算這段的工時
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
                        print(f"    工時: {hours:.2f} 小時 (已完成)")
                    except Exception as e:
                        print(f"    工時計算失敗: {e}")
                elif check_in != 'N/A' and check_out == '':
                    # 正在進行的工時段
                    try:
                        in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                        today = datetime.datetime.now().date()
                        in_datetime = datetime.datetime.combine(today, in_time)
                        duration = now - in_datetime
                        hours = duration.total_seconds() / 3600
                        current_work_hours = hours
                        print(f"    工時: {hours:.2f} 小時 (進行中)")
                    except Exception as e:
                        print(f"    當前工時計算失敗: {e}")
                        current_work_hours = 0
            
            # 總工時 = 已完成的工時 + 當前正在進行的工時
            total_work_hours += current_work_hours
            print(f"\n📊 已完成工時: {total_work_hours - current_work_hours:.2f} 小時")
            print(f"📊 當前工時: {current_work_hours:.2f} 小時")
            print(f"📊 總工時: {total_work_hours:.2f} 小時")
            
            # 檢查當前狀態
            current_status = AttendanceParser.get_current_status(attendance_records)
            print(f"📱 當前狀態: {current_status}")
            
            if current_status == "checked_out":
                print("✅ 今天已經下班了")
                if total_work_hours >= 8:
                    print(f"🎉 恭喜！今天工時充足 ({total_work_hours:.2f} 小時)")
                else:
                    print(f"⚠️ 今天工時不足 ({total_work_hours:.2f} 小時 < 8 小時)")
                return
            
            # 計算還需要多少工時
            remaining_hours = 8 - total_work_hours
            print(f"⏰ 還需要工時: {remaining_hours:.2f} 小時")
            
            if remaining_hours <= 0:
                print("🎉 已經滿8小時了！可以下班了！")
                return
            
            # 計算下班時間
            if current_status == "checked_in":
                # 如果正在上班，計算還需要多少時間
                if remaining_hours > 0:
                    # 從現在開始，還需要工作 remaining_hours 小時
                    checkout_time = now + datetime.timedelta(hours=remaining_hours)
                    print(f"⏰ 滿8小時的下班時間: {checkout_time.strftime('%H:%M')}")
                    
                    # 計算還需要多少時間
                    time_remaining = checkout_time - now
                    if time_remaining.total_seconds() > 0:
                        remaining_minutes = int(time_remaining.total_seconds() / 60)
                        print(f"⏳ 還需要工作: {remaining_minutes} 分鐘")
                    else:
                        print("🎉 已經可以下班了！")
                else:
                    print("🎉 已經滿8小時了！可以下班了！")
            else:
                print("ℹ️ 當前未在上班狀態，無法計算下班時間")
                
        except Exception as e:
            print(f"❌ 計算工時失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def force_punch(self, label=""):
        """強制打卡 - 直接執行打卡動作但會先確認狀態"""
        print(f"🔨 強制打卡模式: {label}")
        
        # 檢查基本條件
        if not Config.AUTO_CHECKIN_ENABLED:
            print("⏸ 已停用自動打卡 (AUTO_CHECKIN_ENABLED=false)")
            return False

        if Config.is_skip_today():
            print("⏸ 今天在請假日列表中，跳過打卡")
            return False

        today = datetime.datetime.today().weekday()
        if today not in Config.WORK_DAYS:
            print(f"⏸ 今天不是工作日，跳過 {label}")
            return False

        # 獲取當天的打卡記錄來判斷當前狀態
        attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
        current_status = AttendanceParser.get_current_status(attendance_records)
        
        print(f"📊 當前打卡狀態: {current_status}")
        print(f"📝 打卡記錄數量: {len(attendance_records)}")
        
        # 顯示打卡記錄
        if attendance_records:
            print("📋 今日打卡記錄:")
            for i, record in enumerate(attendance_records, 1):
                check_in = record.get('check_in', 'N/A')
                check_out = record.get('check_out', 'N/A')
                print(f"  第 {i} 次: Check in={check_in}, Check out={check_out}")
        
        # 查找打卡按鈕
        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
        if not buttons:
            print("❌ 找不到打卡按鈕")
            return False
        
        btn = buttons[0]
        btn_text = btn.text.strip()
        print(f"🔘 找到按鈕: {btn_text}")
        
        # 狀態確認
        print(f"\n🔍 狀態確認:")
        print(f"   當前狀態: {current_status}")
        print(f"   按鈕文字: {btn_text}")
        print(f"   要執行的動作: {label}")
        
        # 檢查狀態是否合理
        status_valid = False
        if label == "上班":
            if current_status == "not_checked_in" and "Check in" in btn_text:
                status_valid = True
                print("   ✅ 狀態合理: 未打卡 → 上班打卡")
            else:
                print(f"   ⚠️ 狀態可能不合理: 當前狀態={current_status}, 按鈕={btn_text}")
                
        elif label == "午休下班":
            if current_status == "checked_in" and "Check out" in btn_text:
                status_valid = True
                print("   ✅ 狀態合理: 已上班 → 午休下班")
            else:
                print(f"   ⚠️ 狀態可能不合理: 當前狀態={current_status}, 按鈕={btn_text}")
                
        elif label == "午休上班":
            if (current_status == "checked_out" or current_status == "not_checked_in") and "Check in" in btn_text:
                status_valid = True
                if current_status == "checked_out":
                    print("   ✅ 狀態合理: 已下班 → 午休上班")
                else:
                    print("   ✅ 狀態合理: 未打卡 → 午休上班")
            else:
                print(f"   ⚠️ 狀態可能不合理: 當前狀態={current_status}, 按鈕={btn_text}")
                
        elif label == "下班":
            if current_status == "checked_in" and "Check out" in btn_text:
                status_valid = True
                print("   ✅ 狀態合理: 已上班 → 下班打卡")
                
                # 對於下班打卡，檢查工時
                if attendance_records:
                    total_work_hours = 0
                    current_work_hours = 0
                    now = datetime.datetime.now()
                    
                    for record in attendance_records:
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
                            except Exception as e:
                                print(f"   ⚠️ 工時計算失敗: {e}")
                        elif check_in != 'N/A' and check_out == '':
                            # 正在進行的工時段
                            try:
                                in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                                today = datetime.datetime.now().date()
                                in_datetime = datetime.datetime.combine(today, in_time)
                                duration = now - in_datetime
                                hours = duration.total_seconds() / 3600
                                current_work_hours = hours
                            except Exception as e:
                                print(f"   ⚠️ 當前工時計算失敗: {e}")
                    
                    total_work_hours += current_work_hours
                    print(f"   📊 總工時: {total_work_hours:.2f} 小時")
                    
                    if total_work_hours < 8:
                        print(f"   ⚠️ 工時不足 ({total_work_hours:.2f}小時 < 8小時)")
                        remaining_hours = 8 - total_work_hours
                        remaining_minutes = int(remaining_hours * 60)
                        print(f"   💡 還需要工作: {remaining_minutes} 分鐘")
                    else:
                        print(f"   ✅ 工時充足 ({total_work_hours:.2f}小時 >= 8小時)")
            else:
                print(f"   ⚠️ 狀態可能不合理: 當前狀態={current_status}, 按鈕={btn_text}")
        
        # 詢問是否繼續
        if not status_valid:
            print(f"\n⚠️ 警告: 狀態可能不合理，但將繼續執行 {label} 打卡")
        
        print(f"\n🚀 執行 {label} 打卡...")
        
        try:
            # 執行打卡
            btn.click()
            print(f"✅ {label} 打卡成功")
            
            # 更新上班時間（如果是上班打卡）
            if label == "上班":
                self.work_start_time = datetime.datetime.now()
                print(f"🕘 更新上班時間: {self.work_start_time}")
            
            # 發送通知
            EmailService.send_checkin_notification(
                f"{label} 打卡成功", 
                label, 
                source="強制打卡",
                attendance_records=attendance_records
            )
            
            return True
            
        except Exception as e:
            print(f"❌ {label} 打卡失敗: {e}")
            EmailService.send_checkin_notification(
                f"{label} 打卡失敗: {e}", 
                label, 
                source="強制打卡"
            )
            return False

    def auto_checkout_when_ready(self):
        """自動偵測下班時間並在滿8小時後打卡下班"""
        print("🕐 開始偵測下班時間...")
        
        # 檢查基本條件
        if not Config.AUTO_CHECKIN_ENABLED:
            print("⏸ 已停用自動打卡 (AUTO_CHECKIN_ENABLED=false)")
            return False

        if Config.is_skip_today():
            print("⏸ 今天在請假日列表中，跳過打卡")
            return False

        today = datetime.datetime.today().weekday()
        if today not in Config.WORK_DAYS:
            print(f"⏸ 今天不是工作日，跳過打卡")
            return False

        try:
            # 獲取當天的打卡記錄
            attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
            current_status = AttendanceParser.get_current_status(attendance_records)
            
            print(f"📊 當前打卡狀態: {current_status}")
            print(f"📝 打卡記錄數量: {len(attendance_records)}")
            
            # 顯示打卡記錄
            if attendance_records:
                print("📋 今日打卡記錄:")
                for i, record in enumerate(attendance_records, 1):
                    check_in = record.get('check_in', 'N/A')
                    check_out = record.get('check_out', 'N/A')
                    print(f"  第 {i} 次: Check in={check_in}, Check out={check_out}")
            
            # 檢查是否正在上班
            if current_status != "checked_in":
                print(f"⚠️ 當前狀態不是 'checked_in'，無法執行自動下班打卡")
                print(f"   當前狀態: {current_status}")
                return False
            
            # 計算當前工時
            now = datetime.datetime.now()
            total_work_hours = 0
            current_work_hours = 0
            
            for record in attendance_records:
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
                        print(f"  ✅ 已完成工時段: {check_in}-{check_out} = {hours:.2f}小時")
                    except Exception as e:
                        print(f"  ⚠️ 工時計算失敗: {e}")
                elif check_in != 'N/A' and check_out == '':
                    # 正在進行的工時段
                    try:
                        in_time = datetime.datetime.strptime(check_in, "%H:%M").time()
                        today = datetime.datetime.now().date()
                        in_datetime = datetime.datetime.combine(today, in_time)
                        duration = now - in_datetime
                        hours = duration.total_seconds() / 3600
                        current_work_hours = hours
                        print(f"  🔄 正在進行工時段: {check_in}-現在 = {hours:.2f}小時")
                    except Exception as e:
                        print(f"  ⚠️ 當前工時計算失敗: {e}")
            
            # 總工時
            total_work_hours += current_work_hours
            print(f"\n📊 總工時: {total_work_hours:.2f} 小時")
            
            # 檢查是否已經滿8小時
            if total_work_hours >= 8:
                print("🎉 已經滿8小時了！可以立即下班打卡")
                
                # 查找下班按鈕
                buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check out')]")
                if not buttons:
                    print("❌ 找不到下班按鈕")
                    return False
                
                btn = buttons[0]
                print(f"🔘 找到下班按鈕: {btn.text.strip()}")
                
                # 執行下班打卡
                try:
                    btn.click()
                    print("✅ 下班打卡成功！")
                    
                    # 發送通知
                    EmailService.send_checkin_notification(
                        f"自動下班打卡成功 (工時: {total_work_hours:.2f}小時)", 
                        "下班", 
                        work_hours=total_work_hours,
                        source="自動下班偵測",
                        attendance_records=attendance_records
                    )
                    
                    return True
                except Exception as e:
                    print(f"❌ 下班打卡失敗: {e}")
                    return False
            else:
                # 計算還需要多少時間
                remaining_hours = 8 - total_work_hours
                remaining_minutes = int(remaining_hours * 60)
                print(f"⏰ 還需要工作: {remaining_minutes} 分鐘 ({remaining_hours:.2f} 小時)")
                
                # 計算下班時間
                checkout_time = now + datetime.timedelta(hours=remaining_hours)
                print(f"🕐 預計下班時間: {checkout_time.strftime('%H:%M:%S')}")
                
                # 計算等待時間（滿8小時後再等1分鐘）
                wait_time = remaining_hours + (1/60)  # 加1分鐘
                wait_minutes = int(wait_time * 60)
                target_time = now + datetime.timedelta(minutes=wait_minutes)
                
                print(f"⏳ 將在 {target_time.strftime('%H:%M:%S')} 自動執行下班打卡")
                print(f"   等待時間: {wait_minutes} 分鐘")
                
                # 發送通知
                EmailService.send_checkin_notification(
                    f"自動下班偵測啟動 - 將在 {target_time.strftime('%H:%M')} 自動打卡下班", 
                    "下班偵測", 
                    work_hours=total_work_hours,
                    source="自動下班偵測",
                    attendance_records=attendance_records
                )
                
                # 等待到目標時間
                print(f"\n⏰ 開始等待... (按 Ctrl+C 取消)")
                try:
                    import time
                    while datetime.datetime.now() < target_time:
                        time.sleep(30)  # 每30秒檢查一次
                        remaining = target_time - datetime.datetime.now()
                        if remaining.total_seconds() > 0:
                            remaining_min = int(remaining.total_seconds() / 60)
                            remaining_sec = int(remaining.total_seconds() % 60)
                            print(f"⏳ 還需要等待: {remaining_min}分{remaining_sec}秒")
                    
                    print(f"\n🚀 時間到了！開始執行下班打卡...")
                    
                    # 重新獲取最新狀態
                    attendance_records = AttendanceParser.get_today_attendance_records(self.driver)
                    current_status = AttendanceParser.get_current_status(attendance_records)
                    
                    if current_status != "checked_in":
                        print(f"⚠️ 狀態已改變: {current_status}，無法執行下班打卡")
                        return False
                    
                    # 查找下班按鈕
                    buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check out')]")
                    if not buttons:
                        print("❌ 找不到下班按鈕")
                        return False
                    
                    btn = buttons[0]
                    print(f"🔘 找到下班按鈕: {btn.text.strip()}")
                    
                    # 執行下班打卡
                    btn.click()
                    print("✅ 自動下班打卡成功！")
                    
                    # 發送成功通知
                    EmailService.send_checkin_notification(
                        f"自動下班打卡成功！", 
                        "下班", 
                        source="自動下班偵測",
                        attendance_records=attendance_records
                    )
                    
                    return True
                    
                except KeyboardInterrupt:
                    print("\n⏸ 用戶取消等待")
                    return False
                except Exception as e:
                    print(f"❌ 等待過程出錯: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 自動下班偵測失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def quit(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
