# 自動打卡系統 (Auto Check-in System)

這是一個基於 Python 和 Selenium 的自動打卡系統，可以自動執行上班、午休下班、午休上班、下班等打卡動作，並支援郵件通知功能。

## 功能特色

- 🕘 **自動排程打卡**: 支援上班、午休下班、午休上班、下班四個時段的自動打卡
- 📧 **郵件通知**: 每次打卡後自動發送結果通知郵件
- 🗓️ **請假日管理**: 支援設定特定日期跳過打卡
- ⏰ **工時檢查**: 自動檢查是否滿 8 小時，未滿則延後下班打卡
- 🖥️ **無頭模式**: 使用 Chrome 無頭模式，不影響其他工作
- 📝 **工作日設定**: 僅在工作日執行打卡（週一至週五）
- 🧠 **智能狀態判斷**: 自動分析當天打卡記錄，避免重複打卡
- 🔍 **多重解析方法**: 使用多種方法解析打卡時間，提高成功率

## 系統需求

- Python 3.7+
- Google Chrome 瀏覽器
- ChromeDriver（會自動下載）

## 安裝步驟

### 1. 克隆專案

```bash
git clone <repository-url>
cd auto-checkin
```

### 2. 建立虛擬環境

```bash
python -m venv venv
```

### 3. 啟動虛擬環境

**macOS/Linux:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
venv\Scripts\activate
```

### 4. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 5. 設定環境變數

在專案根目錄建立 `.env` 檔案：

```env
# 基本設定
USERNAME=你的使用者名稱
PASSWORD=你的密碼
LOGIN_URL=打卡系統的登入網址

# 自動打卡開關
AUTO_CHECKIN_ENABLED=true

# 請假日設定（格式：YYYY-MM-DD，多個日期用逗號分隔）
SKIP_DATES=2024-01-01,2024-02-10,2024-02-11

# 郵件通知設定
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=你的Gmail帳號
SMTP_PASS=你的Gmail應用程式密碼
EMAIL_TO=接收通知的郵件地址
```

### 6. Gmail 應用程式密碼設定

如果使用 Gmail 作為 SMTP 伺服器，需要設定應用程式密碼：

1. 前往 [Google 帳戶設定](https://myaccount.google.com/)
2. 選擇「安全性」→「2 步驟驗證」
3. 在「應用程式密碼」中產生新的密碼
4. 將產生的密碼填入 `.env` 檔案的 `SMTP_PASS`

## 使用方法

### 啟動程式

**正常模式（自動打卡）:**

```bash
python main.py
```

**測試模式（查看打卡記錄）:**

```bash
python main.py test
```

**調試模式（檢查 HTML 結構）:**

```bash
python main.py debug
```

程式啟動後會顯示：

```
🔔 自動打卡程式啟動...
💡 提示:
   - 使用 'python main.py test' 來測試打卡記錄解析
   - 使用 'python main.py debug' 來調試 HTML 結構
```

### 預設打卡時間

- **08:45** - 上班打卡
- **12:00** - 午休下班打卡
- **13:00** - 午休上班打卡
- **17:46** - 下班打卡

### 測試功能

使用測試模式可以查看當天的打卡記錄和解析結果：

```bash
python main.py test
```

測試模式會顯示：

- 🌐 連接狀態
- 🔐 登入結果
- 🕘 解析到的上班時間
- 📊 打卡記錄數量
- 📝 詳細的打卡記錄（包含工時計算）
- 🔘 可用的打卡按鈕

**測試輸出範例：**

```
🧪 開始測試打卡記錄解析...
🌐 正在連接到: https://attendance.company.com
🔐 正在登入...
📋 正在解析打卡記錄...
🕘 上班時間: 2024-09-03 08:50:00
📊 打卡記錄數量: 2
📝 詳細打卡記錄:
  第 1 次:
    Check in:  08:50
    Check out: 12:01
    工時: 3.18 小時
  第 2 次:
    Check in:  13:01
    Check out: N/A
    工時: 進行中...
🔘 找到 1 個打卡按鈕:
  按鈕 1: Check out
✅ 測試完成
```

### 調試功能

如果測試模式無法正常解析打卡記錄，可以使用調試模式來檢查 HTML 結構：

```bash
python main.py debug
```

調試模式會顯示：

- 📅 頁面中所有包含日期的 div 元素
- 🕐 頁面中所有找到的時間格式
- 📦 所有邊框容器的結構和內容

**調試輸出範例：**

```
🔍 開始調試 HTML 結構...
🌐 正在連接到: https://attendance.company.com
🔐 正在登入...
🔍 檢查頁面結構...
📅 找到 15 個包含日期的 div:
  1: 09/03 (Wed)
  2: 09/02 (Tue)
  3: 09/01 (Mon)
  ...
🕐 頁面中找到的所有時間: ['08:50', '12:01', '13:01', '08:50', '12:12', '13:14', '17:53']
📦 找到 4 個邊框容器:
  容器 1: border border-bottom-0 px-3 mb-3
    文本: 09/03 (Wed) Total: 3.18 hours | 03:11 Check in: 08:50 Check out: 12:01 Subtotal: 03:11...
  容器 2: border border-bottom-0 px-3 mb-3
    文本: 09/02 (Tue) Total: 8.02 hours | 08:01 Check in: 08:50 Check out: 12:12 Subtotal: 03:22...
✅ 調試完成
```

### 程式特色

1. **智能工時檢查**: 下班時會檢查是否已工作滿 8 小時，未滿則自動延後打卡時間
2. **請假日跳過**: 在 `SKIP_DATES` 中設定的日期會自動跳過打卡
3. **工作日限制**: 僅在週一至週五執行打卡
4. **郵件通知**: 每次打卡後會發送結果通知到指定郵件
5. **智能狀態判斷**: 程式會自動分析當天的打卡記錄，判斷當前狀態（未上班、已上班、已下班），避免重複打卡
6. **多重解析方法**: 使用三種不同的方法解析打卡時間，提高成功率：
   - 標準格式解析（尋找 "Check in:" 標籤）
   - 備用格式解析（尋找時間格式的 span 元素）
   - 正則表達式解析（從所有文本中提取時間）
7. **測試功能**: 提供獨立的測試模式，可以查看當天的打卡記錄和解析結果

## 環境變數說明

| 變數名稱               | 說明                 | 範例                             |
| ---------------------- | -------------------- | -------------------------------- |
| `USERNAME`             | 打卡系統的使用者名稱 | `john.doe`                       |
| `PASSWORD`             | 打卡系統的密碼       | `mypassword123`                  |
| `LOGIN_URL`            | 打卡系統的登入網址   | `https://attendance.company.com` |
| `AUTO_CHECKIN_ENABLED` | 是否啟用自動打卡     | `true` 或 `false`                |
| `SKIP_DATES`           | 跳過打卡的日期       | `2024-01-01,2024-02-10`          |
| `SMTP_SERVER`          | SMTP 伺服器          | `smtp.gmail.com`                 |
| `SMTP_PORT`            | SMTP 埠號            | `587`                            |
| `SMTP_USER`            | SMTP 使用者名稱      | `your.email@gmail.com`           |
| `SMTP_PASS`            | SMTP 密碼            | `your_app_password`              |
| `EMAIL_TO`             | 接收通知的郵件       | `notify@company.com`             |

## 故障排除

### 常見問題

1. **ChromeDriver 錯誤**

   - 確保已安裝最新版本的 Google Chrome
   - 程式會自動下載對應的 ChromeDriver

2. **登入失敗**

   - 檢查 `USERNAME`、`PASSWORD` 和 `LOGIN_URL` 是否正確
   - 確認打卡系統的網址沒有變更

3. **郵件發送失敗**

   - 檢查 SMTP 設定是否正確
   - 確認 Gmail 應用程式密碼是否有效
   - 檢查網路連線

4. **找不到打卡按鈕**
   - 可能是打卡系統的網頁結構有變更
   - 檢查 `LOGIN_URL` 是否正確

### 日誌查看

程式執行時會在終端機顯示詳細的執行日誌，包括：

- 打卡結果
- 錯誤訊息
- 郵件發送狀態

## 注意事項

- 請確保電腦在打卡時間保持開機狀態
- 建議在穩定的網路環境下執行
- 定期檢查打卡系統是否有更新，可能需要調整程式碼
- 請遵守公司的打卡政策

## 授權

此專案僅供學習和個人使用，請勿用於商業用途。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善此專案。
