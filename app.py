"""
自動打卡系統 Web 介面
使用 Flask 提供前端頁面來管理打卡時間和顯示記錄
"""
import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from web_automation import WebAutomation
from email_service import EmailService
from attendance_parser import AttendanceParser

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生產環境中應該使用更安全的密鑰

# 打卡時間設定檔案路徑
SCHEDULE_FILE = 'schedule_config.json'

def load_schedule_config():
    """載入打卡時間設定"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"載入設定檔案失敗: {e}")
    
    # 預設設定
    return {
        "check_in_time": "08:45",
        "lunch_out_time": "12:00", 
        "lunch_in_time": "13:00",
        "check_out_time": "17:46",
        "enabled": True
    }

def save_schedule_config(config):
    """儲存打卡時間設定"""
    try:
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"儲存設定檔案失敗: {e}")
        return False

def get_attendance_logs():
    """獲取打卡記錄日誌"""
    log_file = 'attendance_log.txt'
    logs = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只顯示最近 50 條記錄
                for line in lines[-50:]:
                    line = line.strip()
                    if line:
                        logs.append(line)
        except Exception as e:
            print(f"讀取日誌檔案失敗: {e}")
    
    return logs

@app.route('/')
def index():
    """首頁"""
    config = load_schedule_config()
    logs = get_attendance_logs()
    
    return render_template('index.html', 
                         config=config, 
                         logs=logs,
                         current_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/update_schedule', methods=['POST'])
def update_schedule():
    """更新打卡時間設定"""
    try:
        config = {
            "check_in_time": request.form.get('check_in_time'),
            "lunch_out_time": request.form.get('lunch_out_time'),
            "lunch_in_time": request.form.get('lunch_in_time'),
            "check_out_time": request.form.get('check_out_time'),
            "enabled": request.form.get('enabled') == 'on'
        }
        
        if save_schedule_config(config):
            return jsonify({"success": True, "message": "設定已更新"})
        else:
            return jsonify({"success": False, "message": "設定更新失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"錯誤: {str(e)}"})

@app.route('/manual_checkin', methods=['POST'])
def manual_checkin():
    """手動執行打卡"""
    try:
        action = request.form.get('action')
        
        # 創建 WebAutomation 實例並執行打卡
        automation = WebAutomation()
        automation.setup_driver()
        
        if automation.login():
            try:
                # 使用 punch_in 方法，它會根據當前狀態自動判斷打卡動作
                automation.punch_in(action)
                result = f"{action} 打卡完成"
                
                # 記錄到日誌
                log_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 手動{action}: {result}"
                with open('attendance_log.txt', 'a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
                
                return jsonify({"success": True, "message": f"打卡成功: {result}"})
            except Exception as e:
                return jsonify({"success": False, "message": f"打卡執行失敗: {str(e)}"})
            finally:
                automation.quit()
        else:
            automation.quit()
            return jsonify({"success": False, "message": "登入失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"打卡失敗: {str(e)}"})

@app.route('/get_attendance_status')
def get_attendance_status():
    """獲取當前打卡狀態"""
    try:
        automation = WebAutomation()
        automation.setup_driver()
        
        if automation.login():
            # 獲取打卡記錄
            records = AttendanceParser.get_today_attendance_records(automation.driver)
            status = AttendanceParser.get_current_status(records)
            work_hours = AttendanceParser.calculate_work_hours(records)
            
            automation.quit()
            
            return jsonify({
                "success": True,
                "status": status,
                "records": records,
                "work_hours": round(work_hours, 2)
            })
        else:
            automation.quit()
            return jsonify({"success": False, "message": "登入失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取狀態失敗: {str(e)}"})

@app.route('/test_email')
def test_email():
    """測試郵件功能"""
    try:
        result = EmailService.test_email()
        if result:
            return jsonify({"success": True, "message": "郵件測試成功"})
        else:
            return jsonify({"success": False, "message": "郵件測試失敗"})
    except Exception as e:
        return jsonify({"success": False, "message": f"郵件測試錯誤: {str(e)}"})

@app.route('/logs')
def logs():
    """日誌頁面"""
    logs = get_attendance_logs()
    return render_template('logs.html', logs=logs)


if __name__ == '__main__':
    print("🌐 啟動自動打卡系統 Web 介面...")
    print("📱 請在瀏覽器中開啟: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
