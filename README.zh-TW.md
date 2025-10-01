# Sentry Issue 匯出工具

將 Sentry 錯誤報告匯出為純文字檔案，方便離線分析與除錯。

## 功能特色

- 匯出完整的錯誤訊息和堆疊追蹤
- 支援 Self-hosted Sentry 和 SaaS 版本
- 包含 Request 資訊、Breadcrumbs 和 Context 資料
- 顯示程式碼片段和變數值
- Debug 模式可檢查完整資料結構
- 批次匯出多個 issues

## 安裝

### 需求

- Python 3.6+
- `requests` 函式庫

### 設定

```bash
# 安裝相依套件
pip install requests

# 下載腳本
# 將腳本儲存為 export_sentry_issue.py
```

## 取得所需資訊

### 1. 取得 Auth Token

1. 登入 Sentry
2. 前往：**Settings** → **Account** → **API** → **Auth Tokens**
3. 點選 **Create New Token**
4. 設定權限（最低需求）：
   - ✅ `event:read`
5. 複製產生的 Token

### 2. 取得 Base URL

**SaaS 版本：**
```
https://sentry.io/api/0/projects/{org-slug}/{project-slug}/issues/
```

**Self-hosted 版本：**
```
https://your-sentry-domain.com/api/0/projects/{org-slug}/{project-slug}/issues/
```

**如何找到 org-slug 和 project-slug：**
- 在 Sentry UI 中，檢查瀏覽器網址列
- 格式：`https://sentry.io/organizations/{org-slug}/projects/{project-slug}/`

### 3. 取得 Issue ID

- 在 Issue 詳細頁面中，網址最後的數字就是 Issue ID
- 範例：`https://sentry.io/organizations/my-org/issues/12345/` → Issue ID 是 `12345`

## 使用方式

### 基本用法

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890" \
  --token "your_sentry_token"
```

### 指定輸出檔案

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345" \
  --token "your_token" \
  --output "critical_errors.txt"
```

### Debug 模式

當資料不完整時，使用 debug 模式檢查原始資料結構：

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345" \
  --token "your_token" \
  --debug
```

Debug 模式會：
- 顯示可用的資料欄位
- 標示遺失的資訊
- 儲存原始 JSON 檔案（`debug_issue_{id}.json`）

## 參數說明

| 參數 | 必要 | 說明 | 範例 |
|------|------|------|------|
| `--base-url` | ✅ | Sentry API base URL | `https://sentry.io/api/0/projects/org/proj/issues/` |
| `--ids` | ✅ | Issue ID 列表，用逗號分隔 | `12345,67890,11111` |
| `--token` | ✅ | Sentry Auth Token | `sntrys_xxx...` |
| `--output` | ❌ | 輸出檔案名稱 | `errors.txt`（預設：`sentry_issues_TIMESTAMP.txt`） |
| `--debug` | ❌ | 啟用 debug 模式 | - |

## 匯出內容

匯出的文字檔案包含以下資訊：

### 基本資訊
- Issue ID、標題、狀態
- 發生次數
- 首次/最後發生時間
- 永久連結

### 詳細資訊
- **錯誤訊息**：例外類型和訊息
- **堆疊追蹤**：完整呼叫堆疊
  - 檔案路徑和行號
  - 函式名稱
  - 程式碼片段
  - 變數值
- **Request 資訊**：URL、Method、Query String、Headers
- **Breadcrumbs**：操作軌跡（包含資料庫查詢）
- **使用者資訊**：User ID、Email、IP
- **Context 資訊**：瀏覽器、作業系統、執行環境
- **Tags**：自訂標籤
- **Extra 資訊**：額外的除錯資料

## 範例

### 範例 1：匯出單一 Issue

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "issue_349.txt"
```

### 範例 2：批次匯出多個 Issues

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349,350,351,352,353" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "batch_export.txt"
```

### 範例 3：Self-hosted Sentry

```bash
python export_sentry_issue.py \
  --base-url "https://your-sentry-domain.com/api/0/projects/mycompany/backend/issues/" \
  --ids "100,101,102" \
  --token "your_token"
```

## 疑難排解

### 錯誤：403 Forbidden

**原因：** Token 權限不足

**解決方法：**
1. 重新建立 Auth Token
2. 確保勾選以下權限：
   - `event:read`
3. 驗證您是專案成員

### 錯誤：404 Not Found

**原因：** Base URL 或 Issue ID 不正確

**解決方法：**
1. 檢查 Base URL 格式是否正確
2. 驗證 Issue ID 是否存在
3. 在 Sentry UI 中確認 org 和 project 名稱

### 缺少 Breadcrumbs 或 Request 資訊

**原因：** Sentry SDK 功能未啟用

**解決方法：**

在您的應用程式中啟用 `send_default_pii`：

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-dsn",
    send_default_pii=True,  # 啟用 Request 和 User 資訊
    traces_sample_rate=1.0,  # 啟用效能追蹤
)
```

**使用 debug 模式檢查：**
```bash
python export_sentry_issue.py --base-url "..." --ids "123" --token "..." --debug
```

檢查 `debug_issue_123.json` 以查看實際可用的資料。

### Token 過期

**解決方法：**
1. 前往 Sentry → Settings → API → Auth Tokens
2. 刪除舊的 Token
3. 建立新的 Token

## 進階用法

### 追蹤 N+1 Query 問題

要有效追蹤 N+1 查詢，請在您的應用程式中啟用資料庫查詢追蹤：

**Django 範例：**
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,  # 追蹤所有交易
    send_default_pii=True,
)
```

Breadcrumbs 會顯示每個資料庫查詢及其執行時間。

### 效能分析

啟用 Performance Monitoring 以取得更詳細的效能資料：

```python
sentry_sdk.init(
    dsn="your-dsn",
    traces_sample_rate=1.0,  # 100% 取樣
    profiles_sample_rate=1.0,  # 啟用 profiling
)
```

### 自動化腳本

將常用指令包裝成 shell 腳本：

```bash
#!/bin/bash
# export_today_errors.sh

python export_sentry_issue.py \
  --base-url "$SENTRY_BASE_URL" \
  --ids "$1" \
  --token "$SENTRY_TOKEN" \
  --output "errors_$(date +%Y%m%d).txt"
```

使用方式：
```bash
chmod +x export_today_errors.sh
./export_today_errors.sh "123,456,789"
```

## 常見問題

**Q: 可以匯出所有未解決的 issues 嗎？**

A: 此腳本需要指定 Issue ID。要批次匯出，請先使用 Sentry API 列出所有 issues，然後提取 ID：

```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://sentry.io/api/0/projects/org/project/issues/?query=is:unresolved" \
  | jq '.[].id' | tr '\n' ','
```

**Q: 支援哪些 Sentry 版本？**

A: 支援 Sentry 9.0+ 和所有 SaaS 版本。

**Q: 匯出的資料會包含敏感資訊嗎？**

A: 可能包含：
- 使用者 Email 和 IP 位址
- Request Headers（Authorization 和 Cookie 已過濾）
- 程式碼片段和變數值

請妥善保管匯出的檔案。

**Q: 可以匯出為 JSON 或 CSV 格式嗎？**

A: 目前僅支援純文字格式。若需要 JSON，可使用 debug 模式產生的 JSON 檔案。

## 授權

MIT License
