// 主要 JavaScript 功能

// 全域變數
let autoRefreshInterval;

// 頁面載入完成後執行
document.addEventListener('DOMContentLoaded', function() {
    console.log('自動打卡系統 Web 介面已載入');
    
    // 初始化功能
    initializePage();
    
    // 設定自動重新整理
    setupAutoRefresh();
});

// 初始化頁面
function initializePage() {
    // 檢查是否有錯誤訊息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // 5秒後自動隱藏成功訊息
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
    
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 設定自動重新整理
function setupAutoRefresh() {
    // 每30秒自動重新整理打卡狀態
    autoRefreshInterval = setInterval(() => {
        if (typeof getAttendanceStatus === 'function') {
            getAttendanceStatus();
        }
    }, 30000);
}

// 格式化時間
function formatTime(timeString) {
    if (!timeString) return '-';
    
    try {
        const [hours, minutes] = timeString.split(':');
        return `${hours}:${minutes}`;
    } catch (e) {
        return timeString;
    }
}

// 計算工時
function calculateWorkHours(checkIn, checkOut) {
    if (!checkIn || !checkOut) return '-';
    
    try {
        const inTime = new Date(`2000-01-01 ${checkIn}`);
        const outTime = new Date(`2000-01-01 ${checkOut}`);
        const diff = (outTime - inTime) / (1000 * 60 * 60);
        
        if (diff < 0) {
            // 跨日情況
            const nextDay = new Date(`2000-01-02 ${checkOut}`);
            const diffNextDay = (nextDay - inTime) / (1000 * 60 * 60);
            return `${diffNextDay.toFixed(1)} 小時`;
        }
        
        return `${diff.toFixed(1)} 小時`;
    } catch (e) {
        return '-';
    }
}

// 顯示載入狀態
function showLoading(elementId, message = '載入中...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">載入中...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
    }
}

// 顯示錯誤訊息
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
}

// 顯示成功訊息
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> ${message}
            </div>
        `;
    }
}

// 確認對話框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 複製到剪貼簿
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已複製到剪貼簿', 'success');
    }).catch(err => {
        console.error('複製失敗:', err);
        showToast('複製失敗', 'error');
    });
}

// 顯示 Toast 訊息
function showToast(message, type = 'info') {
    // 創建 toast 元素
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // 創建 toast 容器（如果不存在）
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    // 添加 toast
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // 顯示 toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // 自動移除
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// 驗證時間格式
function validateTimeFormat(timeString) {
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(timeString);
}

// 驗證打卡時間邏輯
function validateScheduleTimes(times) {
    const { check_in_time, lunch_out_time, lunch_in_time, check_out_time } = times;
    
    const errors = [];
    
    // 檢查時間格式
    if (!validateTimeFormat(check_in_time)) {
        errors.push('上班時間格式不正確');
    }
    if (!validateTimeFormat(lunch_out_time)) {
        errors.push('午休下班時間格式不正確');
    }
    if (!validateTimeFormat(lunch_in_time)) {
        errors.push('午休上班時間格式不正確');
    }
    if (!validateTimeFormat(check_out_time)) {
        errors.push('下班時間格式不正確');
    }
    
    // 檢查時間邏輯
    if (check_in_time >= lunch_out_time) {
        errors.push('上班時間不能晚於或等於午休下班時間');
    }
    if (lunch_out_time >= lunch_in_time) {
        errors.push('午休下班時間不能晚於或等於午休上班時間');
    }
    if (lunch_in_time >= check_out_time) {
        errors.push('午休上班時間不能晚於或等於下班時間');
    }
    
    return errors;
}

// 頁面離開時清理
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

// 錯誤處理
window.addEventListener('error', function(e) {
    console.error('JavaScript 錯誤:', e.error);
    showToast('發生錯誤，請重新整理頁面', 'error');
});

// 網路狀態監聽
window.addEventListener('online', function() {
    showToast('網路連線已恢復', 'success');
});

window.addEventListener('offline', function() {
    showToast('網路連線已中斷', 'warning');
});
