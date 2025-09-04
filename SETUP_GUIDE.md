# 自動打卡系統設定指南

## 🚀 快速開始

### 1. Fork 這個 Repository

1. 點擊右上角的 "Fork" 按鈕
2. 將 repository fork 到你的 GitHub 帳號

### 2. 設定 GitHub Secrets

前往你的 repository → Settings → Secrets and variables → Actions

#### 🔐 必填設定

| Secret 名稱 | 說明               | 範例                        |
| ----------- | ------------------ | --------------------------- |
| `USERNAME`  | 打卡系統的帳號     | `your_username`             |
| `PASSWORD`  | 打卡系統的密碼     | `your_password`             |
| `LOGIN_URL` | 打卡系統的登入網址 | `https://example.com/login` |

#### ⚙️ 選填設定

| Secret 名稱            | 說明               | 預設值 | 範例                    |
| ---------------------- | ------------------ | ------ | ----------------------- |
| `AUTO_CHECKIN_ENABLED` | 是否啟用自動打卡   | `true` | `true` 或 `false`       |
| `SKIP_DATES`           | 請假日（逗號分隔） | 空     | `2024-01-01,2024-12-25` |

#### 📧 郵件通知設定（選填）

| Secret 名稱   | 說明                   | 範例                   |
| ------------- | ---------------------- | ---------------------- |
| `SMTP_SERVER` | SMTP 伺服器            | `smtp.gmail.com`       |
| `SMTP_PORT`   | SMTP 埠號              | `587`                  |
| `SMTP_USER`   | 郵件帳號               | `your_email@gmail.com` |
| `SMTP_PASS`   | 郵件密碼或應用程式密碼 | `your_app_password`    |
| `EMAIL_TO`    | 接收通知的郵件地址     | `notify@example.com`   |

### 3. 啟用 GitHub Actions

1. 前往 Actions 標籤
2. 點擊 "I understand my workflows, go ahead and enable them"
3. 確認 "Auto Check-in" workflow 已啟用

### 4. 測試設定

1. 前往 Actions 標籤
2. 找到 "Auto Check-in" workflow
3. 點擊 "Run workflow" 手動觸發測試

## 📅 排程時間

系統會在以下時間自動執行打卡（台灣時間）：

- **08:45** - 上班打卡
- **12:00** - 午休下班打卡
- **13:00** - 午休上班打卡
- **17:46** - 下班打卡

> ⚠️ **注意**：排程只在週一到週五執行

## ⏰ 保持 Repository 活躍

### 60 天規則

GitHub 會自動禁用 60 天內無活動的 repository 的 scheduled workflows。為了避免這個問題：

#### 自動解決方案

本 repository 包含一個 `keepalive.yml` workflow，會每 30 天自動提交一次，保持 repository 活躍。

#### 手動解決方案

如果排程被禁用了：

1. 手動觸發一次 workflow
2. 進行任何 commit 活動
3. 創建 issue 或 PR

### 檢查 Repository 活動狀態

- 前往 repository 首頁
- 查看最後一次 commit 時間
- 確保在 60 天內有活動

## 🔧 進階設定

### 修改排程時間

編輯 `.github/workflows/auto-checkin.yml` 檔案中的 cron 設定：

```yaml
on:
  schedule:
    # 台灣時間 08:45 上班打卡（UTC 00:45）
    - cron: "45 0 * * 1-5"
    # 台灣時間 12:00 午休下班（UTC 04:00）
    - cron: "0 4 * * 1-5"
    # 台灣時間 13:00 午休上班（UTC 05:00）
    - cron: "0 5 * * 1-5"
    # 台灣時間 17:46 下班打卡（UTC 09:46）
    - cron: "46 9 * * 1-5"
```

### 設定請假日

在 `SKIP_DATES` secret 中設定請假日，格式為 `YYYY-MM-DD`，多個日期用逗號分隔：

```
2024-01-01,2024-12-25,2024-02-28
```

### 停用自動打卡

設定 `AUTO_CHECKIN_ENABLED` secret 為 `false` 即可停用自動打卡。

## 📧 郵件通知設定

### Gmail 設定

1. 啟用兩步驟驗證
2. 生成應用程式密碼
3. 使用應用程式密碼作為 `SMTP_PASS`

### 其他郵件服務

- **Outlook**: `smtp-mail.outlook.com`, port `587`
- **Yahoo**: `smtp.mail.yahoo.com`, port `587`
- **自訂 SMTP**: 根據你的郵件服務商設定

## 🐛 故障排除

### 常見問題

#### 1. 排程沒有執行

- 確認 repository 是 public（免費方案限制）
- 檢查最近 60 天內是否有 commit 活動
- 手動觸發一次 workflow 重新啟用排程

> ⚠️ **重要**：GitHub 會自動禁用 60 天內無活動的 repository 的 scheduled workflows

#### 2. 打卡失敗

- 檢查 `USERNAME`、`PASSWORD`、`LOGIN_URL` 是否正確
- 確認打卡系統網址沒有變更
- 查看 Actions 執行記錄中的錯誤訊息

#### 3. 郵件通知沒有收到

- 檢查 SMTP 設定是否正確
- 確認 `SMTP_PASS` 是應用程式密碼（不是登入密碼）
- 檢查垃圾郵件資料夾

### 查看執行記錄

1. 前往 Actions 標籤
2. 點擊最近的執行記錄
3. 查看 "Run auto check-in" 步驟的詳細日誌

## 🔒 安全性注意事項

- 所有敏感資訊都儲存在 GitHub Secrets 中，不會暴露在程式碼中
- 建議定期更換密碼
- 不要將包含真實帳號密碼的程式碼提交到 repository

## 📞 支援

如果遇到問題，請：

1. 檢查本指南的故障排除部分
2. 查看 GitHub Actions 的執行記錄
3. 在 Issues 中回報問題

---

**免責聲明**：本工具僅供學習和個人使用，使用者需自行承擔使用風險。
