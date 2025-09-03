import os
import time
import datetime
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 載入環境變數 ---
load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = os.getenv("LOGIN_URL")
AUTO_CHECKIN_ENABLED = os.getenv("AUTO_CHECKIN_ENABLED", "true").lower() == "true"

# 工作日 0=週一, 6=週日
WORK_DAYS = [0, 1, 2, 3, 4]
work_start_time = None
today_log = []

# 處理請假日
skip_dates_str = os.getenv("SKIP_DATES", "")
SKIP_DATES = set()
if skip_dates_str:
    for d in skip_dates_str.split(","):
        try:
            SKIP_DATES.add(datetime.datetime.strptime(d.strip(), "%Y-%m-%d").date())
        except ValueError:
            print(f"⚠️ 無效日期格式: {d.strip()}，應為 YYYY-MM-DD")

# --- 寄信功能 ---
def send_email(subject, body):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_to = os.getenv("EMAIL_TO")

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"📧 已寄出通知信: {subject}")
    except Exception as e:
        print(f"❌ 寄信失敗: {e}")

# --- 請假日檢查 ---
def is_skip_today():
    today = datetime.date.today()
    if today in SKIP_DATES:
        print(f"⏸ 今天 {today} 在 SKIP_DATES，跳過自動打卡")
        return True
    return False

# --- 抓今日 Check in ---
def get_today_check_in(driver):
    today_str = datetime.datetime.now().strftime("%m/%d")
    try:
        print(f"🔍 正在尋找今日上班時間，日期: {today_str}")
        
        # 方法1: 尋找包含今日日期的 div
        try:
            date_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{today_str}')]")
            print(f"✅ 找到日期 div: {date_div.text}")
            
            # 找到包含這個日期的容器
            container = date_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'border') and contains(@class,'px-3')]")
            print(f"✅ 找到日期容器")
            
        except Exception as e:
            print(f"⚠️ 方法1失敗: {e}")
            # 方法2: 直接尋找包含日期的容器
            try:
                container = driver.find_element(By.XPATH, f"//div[contains(@class,'border') and contains(@class,'px-3') and .//div[contains(text(), '{today_str}')]]")
                print(f"✅ 方法2找到日期容器")
            except Exception as e2:
                print(f"❌ 方法2也失敗: {e2}")
                # 如果找不到今日記錄，使用預設時間
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                work_start = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 找不到今日記錄，備用方法使用預設上班時間: {work_start}")
                return work_start
        
        # 方法3: 使用正則表達式從容器文本中提取第一個時間（排除時區區域）
        try:
            all_text = container.text
            print(f"📝 容器文本: {all_text}")
            
            # 排除時區相關的文本
            timezone_keywords = ['Eastern Time Zone', 'Central Time Zone', 'Mountain Time Zone', 
                               'Pacific Time Zone', 'East Asia Time Zone', 'India Standard Time',
                               'Ann Arbor', 'Pittsburgh', 'Durham', 'Chicago', 'Texas', 'Colorado',
                               'Washington', 'California', 'Taiwan', 'Singapore', 'Malaysia']
            
            # 檢查是否包含時區關鍵字
            is_timezone_section = any(keyword in all_text for keyword in timezone_keywords)
            if is_timezone_section:
                print("⚠️ 檢測到時區區域，跳過此容器")
                # 如果找不到今日記錄，使用預設時間
                today_date = datetime.datetime.now().date()
                fallback_time = datetime.time(hour=9, minute=0)
                work_start = datetime.datetime.combine(today_date, fallback_time)
                print(f"⚠️ 跳過時區區域，備用方法使用預設上班時間: {work_start}")
                return work_start
            
            import re
            time_pattern = r'\b(\d{1,2}:\d{2})\b'
            times = re.findall(time_pattern, all_text)
            print(f"🕐 找到所有時間: {times}")
            
            if times:
                # 取第一個找到的時間作為上班時間
                time_str = times[0]
                today_date = datetime.datetime.now().date()
                check_in_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                work_start = datetime.datetime.combine(today_date, check_in_time)
                print(f"🕘 備用方法偵測到今日上班時間: {work_start}")
                return work_start
            else:
                print("⚠️ 沒有找到時間格式")
                
        except Exception as e:
            print(f"⚠️ 正則表達式解析失敗: {e}")
            
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

# --- 獲取當天打卡記錄 ---
def get_today_attendance_records(driver):
    """獲取當天的完整打卡記錄"""
    today_str = datetime.datetime.now().strftime("%m/%d")
    records = []
    
    try:
        print(f"🔍 正在尋找日期: {today_str}")
        
        # 方法1: 尋找包含今日日期的 div
        try:
            date_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{today_str}')]")
            print(f"✅ 找到日期 div: {date_div.text}")
            
            # 找到包含這個日期的容器
            container = date_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'border') and contains(@class,'px-3')]")
            print(f"✅ 找到日期容器")
            
        except Exception as e:
            print(f"⚠️ 方法1失敗: {e}")
            # 方法2: 直接尋找包含日期的容器
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
                timezone_keywords = ['Eastern Time Zone', 'Central Time Zone', 'Mountain Time Zone', 
                                   'Pacific Time Zone', 'East Asia Time Zone', 'India Standard Time',
                                   'Ann Arbor', 'Pittsburgh', 'Durham', 'Chicago', 'Texas', 'Colorado',
                                   'Washington', 'California', 'Taiwan', 'Singapore', 'Malaysia']
                
                is_timezone_row = any(keyword in row_text for keyword in timezone_keywords)
                if is_timezone_row:
                    print(f"   ⚠️ 第 {i+1} 行是時區行，跳過")
                    continue
                
                # 使用正則表達式提取時間
                import re
                time_pattern = r'\b(\d{1,2}:\d{2})\b'
                times = re.findall(time_pattern, row_text)
                print(f"   找到時間: {times}")
                
                if len(times) >= 1:
                    check_in_time = times[0]
                    check_out_time = times[1] if len(times) > 1 else ""
                    
                    records.append({
                        'check_in': check_in_time,
                        'check_out': check_out_time
                    })
                    print(f"   ✅ 記錄 {i+1}: Check in={check_in_time}, Check out={check_out_time}")
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

# --- 打卡主流程 ---
def punch_in(label=""):
    global work_start_time, today_log

    if not AUTO_CHECKIN_ENABLED:
        print("⏸ 已停用自動打卡 (AUTO_CHECKIN_ENABLED=false)")
        return

    if is_skip_today():
        return

    today = datetime.datetime.today().weekday()
    if today not in WORK_DAYS:
        print(f"⏸ 今天不是工作日，跳過 {label}")
        return

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)

    driver.find_element(By.ID, "__BVID__6").send_keys(USERNAME)
    driver.find_element(By.ID, "__BVID__8").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(),'Log In')]").click()
    time.sleep(3)

    # 獲取當天的打卡記錄來判斷當前狀態
    attendance_records = get_today_attendance_records(driver)
    
    # 優先使用當天第一筆打卡記錄的 Check in 時間作為上班時間
    if attendance_records:
        first_record = attendance_records[0]
        if first_record.get('check_in'):
            try:
                check_in_time_str = first_record['check_in']
                today_date = datetime.datetime.now().date()
                check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
                work_start_time = datetime.datetime.combine(today_date, check_in_time)
                print(f"🕘 使用當天第一筆打卡記錄作為上班時間: {work_start_time}")
            except Exception as e:
                print(f"⚠️ 解析第一筆打卡時間失敗: {e}")
                # 如果解析失敗，使用備用方法
                if not work_start_time:
                    work_start_time = get_today_check_in(driver)
    else:
        # 如果沒有打卡記錄，使用備用方法
        if not work_start_time:
            work_start_time = get_today_check_in(driver)
    
    buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
    if not buttons:
        log_entry = f"{label}: 找不到打卡按鈕"
        today_log.append(log_entry)
        send_email(f"打卡結果: {label}", "\n".join(today_log))
        driver.quit()
        return

    btn = buttons[0]
    btn_text = btn.text.strip()
    
    # 根據打卡記錄判斷當前狀態
    current_status = "unknown"
    if attendance_records:
        last_record = attendance_records[-1]
        if last_record['check_out'] == "":
            current_status = "checked_in"  # 已上班，未下班
        else:
            current_status = "checked_out"  # 已下班
    else:
        current_status = "not_checked_in"  # 尚未上班打卡

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
                if work_start_time:
                    duration = now - work_start_time
                    hours = duration.total_seconds() / 3600
                    if hours < 8:
                        delay_minutes = int((8 - hours) * 60) + 1
                        new_time = now + datetime.timedelta(minutes=delay_minutes)
                        print(f"⏳ 未滿 8 小時，延後到 {new_time.strftime('%H:%M')} 下班打卡")
                        schedule.every().day.at(new_time.strftime("%H:%M")).do(punch_in, label="下班")
                        driver.quit()
                        return
                should_punch = True
                result = "下班打卡成功"
            else:
                result = f"下班打卡 - 當前狀態: {current_status}，按鈕: {btn_text}，略過"
        
        # 執行打卡
        if should_punch:
            btn.click()
            if label == "上班":
                work_start_time = datetime.datetime.now()
        else:
            print(f"⏸ {result}")
            
    except Exception as e:
        result = f"{label} 失敗: {e}"

    # 更新 log
    check_in_time = get_today_check_in(driver)
    log_entry = f"{label}: {result}, Check in: {check_in_time}, Check out: 未抓取"
    today_log.append(log_entry)

    # 寄信通知
    send_email(f"打卡結果: {label}", "\n".join(today_log))

    print(f"📌 {label} 完成: {result}")
    driver.quit()

# ---- 排程 ----
schedule.every().day.at("08:45").do(lambda: punch_in("上班"))
schedule.every().day.at("12:00").do(lambda: punch_in("午休下班"))
schedule.every().day.at("13:00").do(lambda: punch_in("午休上班"))
schedule.every().day.at("17:46").do(lambda: punch_in("下班"))

# --- 調試函數 ---
def debug_html_structure():
    """調試函數：檢查 HTML 結構"""
    print("🔍 開始調試 HTML 結構...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"🌐 正在連接到: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        print("🔐 正在登入...")
        driver.find_element(By.ID, "__BVID__6").send_keys(USERNAME)
        driver.find_element(By.ID, "__BVID__8").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Log In')]").click()
        time.sleep(3)
        
        print("🔍 檢查頁面結構...")
        
        # 檢查所有包含日期的 div
        date_divs = driver.find_elements(By.XPATH, "//div[contains(text(), '/')]")
        print(f"📅 找到 {len(date_divs)} 個包含日期的 div:")
        for i, div in enumerate(date_divs[:10]):  # 只顯示前10個
            print(f"  {i+1}: {div.text}")
        
        # 檢查所有包含時間的文本（排除時區）
        import re
        page_text = driver.page_source
        
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
        containers = driver.find_elements(By.XPATH, "//div[contains(@class,'border') and contains(@class,'px-3')]")
        print(f"📦 找到 {len(containers)} 個邊框容器:")
        for i, container in enumerate(containers):
            print(f"  容器 {i+1}: {container.get_attribute('class')}")
            print(f"    文本: {container.text[:100]}...")
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("✅ 調試完成")

# --- 測試函數 ---
def test_attendance_records():
    """測試函數：打印今天的打卡記錄"""
    print("🧪 開始測試打卡記錄解析...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"🌐 正在連接到: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        print("🔐 正在登入...")
        driver.find_element(By.ID, "__BVID__6").send_keys(USERNAME)
        driver.find_element(By.ID, "__BVID__8").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Log In')]").click()
        time.sleep(3)
        
        print("📋 正在解析打卡記錄...")
        
        # 先檢查頁面內容
        print("🔍 檢查頁面內容...")
        page_source = driver.page_source
        # if "09/03" in page_source:
        #     print("✅ 頁面包含 09/03 日期")
        # else:
        #     print("❌ 頁面不包含 09/03 日期")
        
        # 測試完整打卡記錄
        records = get_today_attendance_records(driver)
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
                    print(f"🕘 使用當天第一筆打卡記錄作為上班時間: {work_start}")
                except Exception as e:
                    print(f"⚠️ 解析第一筆打卡時間失敗: {e}")
                    work_start = get_today_check_in(driver)
                    print(f"🕘 備用方法上班時間: {work_start}")
        else:
            work_start = get_today_check_in(driver)
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
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
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
        driver.quit()
        print("✅ 測試完成")

# --- 主程式 ---
if __name__ == "__main__":
    import sys
    
    # 檢查是否為測試模式
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_attendance_records()
        elif sys.argv[1] == "debug":
            debug_html_structure()
        else:
            print("❌ 未知的參數。可用參數: test, debug")
    else:
        print("🔔 自動打卡程式啟動...")
        print("💡 提示:")
        print("   - 使用 'python main.py test' 來測試打卡記錄解析")
        print("   - 使用 'python main.py debug' 來調試 HTML 結構")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
