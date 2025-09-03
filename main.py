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
        date_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{today_str}')]")
        container = date_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'border')]")
        check_in_elem = container.find_element(By.XPATH, ".//div[contains(text(),'Check in:')]/following-sibling::span")
        check_in_time_str = check_in_elem.text.strip()
        if check_in_time_str:
            today_date = datetime.datetime.now().date()
            check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
            work_start = datetime.datetime.combine(today_date, check_in_time)
            print(f"🕘 偵測到今日上班時間: {work_start}")
            return work_start
    except Exception as e:
        print(f"❌ 讀取 Check in 失敗: {e}")
    return None

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

    try:
        # 判斷點擊邏輯
        if label == "上班" and "Check in" in btn_text:
            btn.click()
            work_start_time = datetime.datetime.now()
            result = "上班打卡成功"
        elif label == "午休下班" and "Check out" in btn_text:
            btn.click()
            result = "午休下班打卡成功"
        elif label == "午休上班" and "Check in" in btn_text:
            btn.click()
            result = "午休上班打卡成功"
        elif label == "下班" and "Check out" in btn_text:
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
            btn.click()
            result = "下班打卡成功"
        else:
            result = f"{label} 已是正確狀態，略過"
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

print("🔔 自動打卡程式啟動...")

while True:
    schedule.run_pending()
    time.sleep(1)
