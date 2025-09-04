# GitHub Actions 自動打卡工作流程指南

## 概述

這個指南說明如何在 GitHub Actions 環境中使用自動打卡系統，包括工時不足時的處理方式。

## 工作流程排程

### 自動排程時間

| 台灣時間 | UTC 時間 | Cron 表達式    | 執行時間範圍 (UTC) | 動作        |
| -------- | -------- | -------------- | ------------------ | ----------- |
| 08:45    | 00:45    | `45 0 * * 1-5` | 00:40-00:50        | 上班打卡    |
| 12:00    | 04:00    | `0 4 * * 1-5`  | 03:55-04:05        | 午休下班    |
| 13:00    | 05:00    | `0 5 * * 1-5`  | 04:55-05:05        | 午休上班    |
| 17:46    | 09:46    | `46 9 * * 1-5` | 09:40-09:50        | 下班打卡(1) |
| 20:00    | 12:00    | `0 12 * * 1-5` | 11:55-12:05        | 下班打卡(2) |
| 22:00    | 14:00    | `0 14 * * 1-5` | 13:55-14:05        | 下班打卡(3) |

### 手動觸發

你可以隨時手動觸發工作流程：

1. 前往 GitHub 倉庫的 Actions 頁面
2. 選擇 "Auto Check-in" 工作流程
3. 點擊 "Run workflow" 按鈕

## 工時檢查機制

### 本地環境

- 如果工時不足 8 小時，系統會自動延後打卡時間
- 延後時間 = 8 小時 - 目前工時 + 1 分鐘

### GitHub Actions 環境

- 如果工時不足 8 小時，系統會：
  1. 發送郵件通知
  2. 記錄工時不足的詳細資訊
  3. 提供手動觸發工作流程的連結
  4. **不會**延後打卡（因為 GitHub Actions 是單次執行）

## 工時不足通知郵件

當工時不足時，你會收到包含以下資訊的郵件：

```
工時檢查結果：
- 目前工時：X.X 小時
- 需要工時：8 小時
- 還需要：XX 分鐘

請手動啟動 GitHub Actions 工作流程來執行下班打卡。

工作流程連結：https://github.com/你的用戶名/你的倉庫名/actions/workflows/auto-checkin.yml
```

## 手動觸發步驟

### 方法一：GitHub 網頁介面

1. 前往你的 GitHub 倉庫
2. 點擊 "Actions" 標籤
3. 選擇 "Auto Check-in" 工作流程
4. 點擊 "Run workflow" 按鈕
5. 選擇分支（通常是 main）
6. 點擊 "Run workflow" 確認

### 方法二：GitHub CLI

```bash
gh workflow run auto-checkin.yml
```

### 方法三：API 調用

```bash
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/你的用戶名/你的倉庫名/actions/workflows/auto-checkin.yml/dispatches \
  -d '{"ref":"main"}'
```

## 設定 Secrets

確保在 GitHub 倉庫中設定以下 Secrets：

| Secret 名稱          | 說明               | 範例                      |
| -------------------- | ------------------ | ------------------------- |
| USERNAME             | 打卡系統使用者名稱 | your_username             |
| PASSWORD             | 打卡系統密碼       | your_password             |
| LOGIN_URL            | 打卡系統登入網址   | https://example.com/login |
| AUTO_CHECKIN_ENABLED | 是否啟用自動打卡   | true                      |
| SKIP_DATES           | 跳過的日期（可選） | 2024-01-01,2024-12-25     |
| SMTP_SERVER          | 郵件伺服器         | smtp.gmail.com            |
| SMTP_PORT            | 郵件埠號           | 587                       |
| SMTP_USER            | 郵件帳號           | your_email@gmail.com      |
| SMTP_PASS            | 郵件密碼           | your_app_password         |
| EMAIL_TO             | 收件人郵件         | notification@example.com  |

## 故障排除

### 常見問題

1. **工時不足但沒有收到郵件**

   - 檢查 SMTP 相關的 Secrets 是否正確設定
   - 確認郵件帳號已啟用兩步驟驗證並使用應用程式密碼

2. **手動觸發失敗**

   - 確認你有倉庫的寫入權限
   - 檢查工作流程檔案語法是否正確

3. **打卡失敗**
   - 檢查 USERNAME、PASSWORD、LOGIN_URL 是否正確
   - 查看 Actions 日誌了解詳細錯誤資訊

### 日誌查看

1. 前往 GitHub 倉庫的 Actions 頁面
2. 點擊失敗的工作流程執行
3. 查看 "Run auto check-in" 步驟的日誌
4. 根據錯誤訊息進行除錯

## 最佳實踐

1. **定期檢查**：建議每天檢查一次 Actions 執行結果
2. **備用方案**：如果自動打卡失敗，及時手動觸發
3. **郵件通知**：確保郵件設定正確，以便接收工時不足通知
4. **測試環境**：在正式使用前，先在測試環境中驗證設定

## 注意事項

- GitHub Actions 有執行時間限制（免費版 6 小時）
- 每個月有免費的執行分鐘數限制
- 建議在非工作時間關閉不必要的排程以節省資源
- 定期更新依賴套件以確保安全性
