from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import schedule
import datetime
import os
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# 從環境變數讀帳號密碼
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = os.getenv("LOGIN_URL")


if not USERNAME or not PASSWORD:
    raise ValueError("❌ 沒有設定帳號或密碼，請檢查 .env 或 GitHub Secrets")
# 帳號密碼 & 登入網址
# USERNAME = "leon.chen@pacston.com"
# PASSWORD = "Leon$123"
# LOGIN_URL = "https://ehr.projectnwork.com/"

# 工作日 (0=週一, 6=週日)
WORK_DAYS = [0, 1, 2, 3, 4]

# 紀錄今天的上班時間
work_start_time = None


def get_today_check_in(driver):
    """讀取 EHR 系統今日的 Check in 時間"""
    today_str = datetime.datetime.now().strftime("%m/%d")  # e.g. "09/03"

    try:
        # 找今天日期的區塊
        date_div = driver.find_element(By.XPATH, f"//div[contains(text(), '{today_str}')]")

        # 找到父層，再找 "Check in:" 後的時間
        container = date_div.find_element(By.XPATH, "./ancestor::div[contains(@class,'border')]")
        check_in_elem = container.find_element(By.XPATH, ".//div[contains(text(),'Check in:')]/following-sibling::span")

        check_in_time_str = check_in_elem.text.strip()
        if check_in_time_str:
            today_date = datetime.datetime.now().date()
            check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M").time()
            work_start_time = datetime.datetime.combine(today_date, check_in_time)
            print(f"🕘 偵測到今日上班時間: {work_start_time}")
            return work_start_time
        else:
            print("⚠️ 今日尚未打卡 (Check in 空白)")
            return None
    except Exception as e:
        print(f"❌ 讀取 Check in 時間失敗: {e}")
        return None


def punch_in(label=""):
    global work_start_time

    today = datetime.datetime.today().weekday()
    if today not in WORK_DAYS:
        print(f"⏸ 今天不是打卡日，跳過 {label}。")
        return

    # 無頭模式設定
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(LOGIN_URL)

    # 登入
    driver.find_element(By.ID, "__BVID__6").send_keys(USERNAME)
    driver.find_element(By.ID, "__BVID__8").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]").click()
    time.sleep(3)

    # 如果還沒記錄上班時間，試著從系統抓
    if not work_start_time:
        work_start_time = get_today_check_in(driver)

    # 找打卡按鈕
    buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Check in') or contains(text(),'Check out')]")
    if not buttons:
        print(f"⚠️ 找不到打卡按鈕 ({label})")
        driver.quit()
        return

    btn = buttons[0]
    btn_text = btn.text.strip()

    # 打卡邏輯
    if label == "上班":
        if "Check in" in btn_text:
            btn.click()
            work_start_time = datetime.datetime.now()
            print("✅ 自動上班打卡完成")
        else:
            print("ℹ️ 已經上班過了，略過")

    elif label in ["午休下班", "午休上班"]:
        if (label == "午休下班" and "Check out" in btn_text) or \
           (label == "午休上班" and "Check in" in btn_text):
            btn.click()
            print(f"✅ {label} 打卡完成")
        else:
            print(f"ℹ️ {label} 已是正確狀態，略過")

    elif label == "下班":
        if "Check out" in btn_text:
            if work_start_time:
                now = datetime.datetime.now()
                duration = now - work_start_time
                hours = duration.total_seconds() / 3600
                if hours < 8:
                    delay_minutes = int((8 - hours) * 60) + 1
                    new_time = now + datetime.timedelta(minutes=delay_minutes)
                    print(f"⏳ 工作未滿 8 小時，延遲到 {new_time.strftime('%H:%M')} 再打卡")
                    schedule.every().day.at(new_time.strftime("%H:%M")).do(punch_in, label="下班")
                    driver.quit()
                    return
            btn.click()
            print("✅ 下班打卡完成")
        else:
            print("ℹ️ 已經下班過了，略過")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📌 {label} 檢查完成 ({now})")

    driver.quit()


# ---- 打卡流程 ----
def morning_check_in():
    punch_in("上班")

def lunch_out():
    punch_in("午休下班")

def lunch_in():
    punch_in("午休上班")

def evening_check_out():
    punch_in("下班")


# ---- 排程設定 ----
schedule.every().day.at("09:00").do(morning_check_in)
schedule.every().day.at("12:00").do(lunch_out)
schedule.every().day.at("13:00").do(lunch_in)
schedule.every().day.at("17:53").do(evening_check_out)

print("🔔 自動打卡程式已啟動...")

while True:
    schedule.run_pending()
    time.sleep(1)
