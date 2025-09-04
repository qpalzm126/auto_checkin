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
from selenium.webdriver.common.by import By
from config import Config
from attendance_parser import AttendanceParser
from email_service import EmailService

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
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def login(self):
        """登入系統"""
        try:
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
                    print("✅ 登入成功 - 找到打卡按鈕")
                    return True
                
                print("❌ 登入失敗 - 未找到登入成功指標")
                return False
                
            except Exception as e:
                print(f"❌ 檢查登入狀態時出錯: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 登入過程出錯: {e}")
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
                    # 如果解析失敗，使用備用方法
                    if not self.work_start_time:
                        self.work_start_time = AttendanceParser.get_today_check_in(self.driver)
        else:
            # 如果沒有打卡記錄，使用備用方法
            if not self.work_start_time:
                self.work_start_time = AttendanceParser.get_today_check_in(self.driver)
        
        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
        if not buttons:
            log_entry = f"{label}: 找不到打卡按鈕"
            self.today_log.append(log_entry)
            EmailService.send_email(f"打卡結果: {label}", "\n".join(self.today_log))
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
                if current_status == "checked_out" and "Check in" in btn_text:
                    should_punch = True
                    result = "午休上班打卡成功"
                else:
                    result = f"午休上班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
                    
            elif label == "下班":
                if current_status == "checked_in" and "Check out" in btn_text:
                    # 檢查工時
                    now = datetime.datetime.now()
                    if self.work_start_time:
                        duration = now - self.work_start_time
                        hours = duration.total_seconds() / 3600
                        if hours < 8:
                            # 在 GitHub Actions 環境中，發送郵件通知而不是延後
                            if os.getenv("GITHUB_ACTIONS"):
                                print(f"⏳ 工時不足 8 小時 (目前: {hours:.1f} 小時)，發送通知郵件")
                                remaining_hours = 8 - hours
                                remaining_minutes = int(remaining_hours * 60)
                                
                                # 發送工時不足通知
                                subject = f"工時不足通知 - 需要再工作 {remaining_minutes} 分鐘"
                                body = f"""
工時檢查結果：
- 目前工時：{hours:.1f} 小時
- 需要工時：8 小時
- 還需要：{remaining_minutes} 分鐘

請手動啟動 GitHub Actions 工作流程來執行下班打卡。

工作流程連結：https://github.com/你的用戶名/你的倉庫名/actions/workflows/auto-checkin.yml
                                """
                                
                                EmailService.send_email(subject, body)
                                result = f"工時不足 ({hours:.1f}小時)，已發送通知郵件"
                                self.driver.quit()
                                return
                            else:
                                # 本地環境：延後打卡
                                delay_minutes = int((8 - hours) * 60) + 1
                                new_time = now + datetime.timedelta(minutes=delay_minutes)
                                print(f"⏳ 未滿 8 小時，延後到 {new_time.strftime('%H:%M')} 下班打卡")
                                schedule.every().day.at(new_time.strftime("%H:%M")).do(self.punch_in, label="下班")
                                self.driver.quit()
                                return
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
        check_in_time = AttendanceParser.get_today_check_in(self.driver)
        log_entry = f"{label}: {result}, Check in: {check_in_time}, Check out: 未抓取"
        self.today_log.append(log_entry)

        # 寄信通知
        EmailService.send_email(f"打卡結果: {label}", "\n".join(self.today_log))

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
                        work_start = AttendanceParser.get_today_check_in(self.driver)
                        print(f"🕘 備用方法上班時間: {work_start}")
            else:
                work_start = AttendanceParser.get_today_check_in(self.driver)
                print(f"🕘 備用方法上班時間: {work_start}")
            
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
                
            # 測試按鈕狀態
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
            if buttons:
                print(f"🔘 找到 {len(buttons)} 個打卡按鈕:")
                for i, btn in enumerate(buttons, 1):
                    print(f"  按鈕 {i}: {btn.text.strip()}")
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
    
    def quit(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
