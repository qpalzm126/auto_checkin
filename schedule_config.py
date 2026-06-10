"""
排程設定管理
將排程時間儲存到 JSON 檔案，方便動態修改
"""
import os
import json
import re


# 預設排程時間（首次執行或重置時使用）
DEFAULT_SCHEDULE_TIMES = [
    {"time": "08:43", "label": "上班"},
    {"time": "12:14", "label": "午休下班"},
    {"time": "13:14", "label": "午休上班"},
    {"time": "17:55", "label": "下班"},
]

# 設定檔路徑
CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schedule_config.json"
)

# 合法的打卡動作名稱
VALID_LABELS = ["上班", "午休下班", "午休上班", "下班"]

# 時間格式 (HH:MM, 24 小時制)
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def validate_time(time_str: str) -> bool:
    """驗證時間格式 (HH:MM)"""
    return bool(TIME_PATTERN.match(time_str))


def load_schedule():
    """
    載入排程設定
    
    Returns:
        list: [{"time": "HH:MM", "label": "..."}]
    """
    if not os.path.exists(CONFIG_FILE):
        # 第一次執行，建立預設檔
        save_schedule(DEFAULT_SCHEDULE_TIMES)
        return list(DEFAULT_SCHEDULE_TIMES)
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("設定檔格式錯誤")
        
        # 驗證每個項目
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("項目必須為物件")
            if "time" not in item or "label" not in item:
                raise ValueError("項目缺少 time 或 label 欄位")
            if not validate_time(item["time"]):
                raise ValueError(f"時間格式錯誤: {item['time']}")
        
        return data
    except Exception as e:
        print(f"⚠️ 載入排程設定失敗 ({e})，使用預設值")
        return list(DEFAULT_SCHEDULE_TIMES)


def save_schedule(schedule_list: list) -> bool:
    """
    儲存排程設定
    
    Args:
        schedule_list: [{"time": "HH:MM", "label": "..."}]
    
    Returns:
        bool: 是否成功
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(schedule_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 儲存排程設定失敗: {e}")
        return False


def update_schedule_time(label: str, new_time: str) -> tuple:
    """
    更新指定動作的排程時間
    
    Args:
        label: 動作名稱（上班/午休下班/午休上班/下班）
        new_time: 新時間 HH:MM
    
    Returns:
        (success: bool, message: str)
    """
    if label not in VALID_LABELS:
        return False, f"無效的動作: {label}\n可用動作: {', '.join(VALID_LABELS)}"
    
    if not validate_time(new_time):
        return False, f"無效的時間格式: {new_time}\n請使用 HH:MM 格式 (24小時制)"
    
    schedule_list = load_schedule()
    
    # 尋找對應的項目
    found = False
    old_time = None
    for item in schedule_list:
        if item["label"] == label:
            old_time = item["time"]
            item["time"] = new_time
            found = True
            break
    
    if not found:
        # 不存在則新增
        schedule_list.append({"time": new_time, "label": label})
        if save_schedule(schedule_list):
            return True, f"✅ 新增排程: {label} → {new_time}"
        return False, "儲存失敗"
    
    if old_time == new_time:
        return True, f"ℹ️ {label} 排程時間沒有變動 ({new_time})"
    
    if save_schedule(schedule_list):
        return True, f"✅ {label} 排程已更新: {old_time} → {new_time}"
    return False, "儲存失敗"


def reset_schedule() -> bool:
    """重置為預設排程"""
    return save_schedule(DEFAULT_SCHEDULE_TIMES)


def get_schedule_as_tuples():
    """
    取得排程列表（轉成 main.py 用的 tuple 格式）
    
    Returns:
        list: [(time_str, label), ...]
    """
    schedule_list = load_schedule()
    return [(item["time"], item["label"]) for item in schedule_list]
