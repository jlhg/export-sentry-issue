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

- Python 3.10+
- `requests` 函式庫（會自動安裝）

### 設定

```bash
pip install export-sentry-issue
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

### 建議作法：安全配置

為了更好的安全性，將憑證儲存到配置檔案，而不是在命令列中傳遞：

```bash
# 步驟 1：初始化（一次性設定）
export-sentry-issue init

# 您將被提示輸入：
# - Base URL: https://sentry.io/api/0/projects/my-org/my-project/issues/
# - Token:（隱藏輸入，不會顯示在螢幕上）

# 步驟 2：使用已儲存的配置匯出 issues
export-sentry-issue export --ids "12345,67890"

# 步驟 3：完成後，撤銷並刪除配置
export-sentry-issue revoke
```

配置會儲存到 `~/.config/export-sentry-issue/config.json`，檔案權限為 600（僅擁有者可讀寫）。

**✓ 安全優勢：**
- Token 不會出現在 shell 歷史記錄中
- Token 不會出現在 process 列表中
- Token 以安全的檔案權限儲存（僅擁有者可讀寫）
- 不需要時可輕鬆撤銷

### 替代方案：命令列參數

您仍可透過命令列提供憑證，適用於 CI/CD 或一次性使用：

```bash
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890" \
  --token "your_sentry_token"
```

**⚠️ 安全警告：** 在命令列使用 `--token` 可能會在以下地方洩漏您的 token：
- Shell 歷史記錄（例如 `~/.bash_history`）
- Process 列表（其他使用者可透過 `ps` 查看）
- 日誌檔案和監控工具

### 替代方案：環境變數

```bash
export SENTRY_TOKEN="your_sentry_token"
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890"
```

### 指定輸出檔案

```bash
export-sentry-issue export \
  --ids "12345" \
  --output "critical_errors.txt"
```

### Debug 模式

當資料不完整時，使用 debug 模式檢查原始資料結構：

```bash
export-sentry-issue export \
  --ids "12345" \
  --debug
```

Debug 模式會：
- 顯示可用的資料欄位
- 標示遺失的資訊
- 儲存原始 JSON 檔案（`debug_issue_{id}.json`）

## 命令說明

### `init` - 初始化配置

安全地儲存您的 Sentry 憑證以供未來使用。

```bash
export-sentry-issue init
```

**功能：**
- 互動式提示輸入 base URL 和 token
- Token 輸入是隱藏的（不會顯示在螢幕上）
- 儲存到 `~/.config/export-sentry-issue/config.json`
- 設定安全的檔案權限（600 - 僅擁有者可讀寫）
- 儲存前驗證 token 有效性
- 允許覆寫現有配置

### `export` - 匯出 Issues

將 Sentry issues 匯出為純文字檔案。

```bash
# 使用已儲存的配置
export-sentry-issue export --ids "12345,67890"

# 自訂輸出檔案
export-sentry-issue export --ids "12345" --output "errors.txt"

# 覆寫已儲存的配置
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/org/proj/issues/" \
  --token "custom_token" \
  --ids "12345"
```

**參數說明：**

| 參數 | 必要 | 說明 |
|------|------|------|
| `--ids` | ✅ 是 | Issue ID 列表，用逗號分隔（例如：`12345,67890,11111`） |
| `--base-url` | ❌ 否* | Sentry API base URL |
| `--token` | ❌ 否* | Sentry Auth Token |
| `--output` | ❌ 否 | 輸出檔案名稱（預設：`sentry_issues_TIMESTAMP.txt`） |
| `--debug` | ❌ 否 | 啟用 debug 模式，顯示可用欄位並儲存原始 JSON |

*僅在未透過 `init` 命令或環境變數配置時為必要

**Token 優先順序（由高到低）：**
1. 命令列 `--token` 參數
2. `SENTRY_TOKEN` 環境變數
3. 已儲存的配置檔案（`~/.config/export-sentry-issue/config.json`）

### `revoke` - 撤銷 Token

刪除已儲存的配置,並取得從 Sentry 撤銷 token 的說明。

```bash
export-sentry-issue revoke
```

**動作：**
- 顯示目前配置詳情（遮蔽的 token）
- 提示確認
- 刪除 `~/.config/export-sentry-issue/config.json`
- 提供從 Sentry UI 手動撤銷 token 的說明

**注意：** 您必須從 Sentry 手動撤銷 token：
1. 前往：**Settings** → **Account** → **API** → **Auth Tokens**
2. 找到並刪除該 token

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

### 範例 1：首次使用（推薦）

```bash
# 使用您的憑證初始化
export-sentry-issue init
# 輸入 base URL: https://sentry.example.com/api/0/projects/my-org/web-app/issues/
# 輸入 token:（隱藏輸入）

# 匯出單一 issue
export-sentry-issue export --ids "349" --output "issue_349.txt"

# 完成後清理
export-sentry-issue revoke
```

### 範例 2：批次匯出多個 Issues

```bash
# 使用已儲存的配置
export-sentry-issue export \
  --ids "349,350,351,352,353" \
  --output "batch_export.txt"
```

### 範例 3：Self-hosted Sentry

```bash
# 使用 self-hosted URL 初始化
export-sentry-issue init
# 輸入 base URL: https://your-sentry-domain.com/api/0/projects/mycompany/backend/issues/
# 輸入 token:（隱藏輸入）

# 匯出 issues
export-sentry-issue export --ids "100,101,102"
```

### 範例 4：一次性匯出（無配置）

```bash
# 用於 CI/CD 或一次性使用
export-sentry-issue export \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "issue_349.txt"
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
export-sentry-issue export --ids "123" --debug
```

檢查 `debug_issue_123.json` 以查看實際可用的資料。

### Token 過期

**解決方法：**
1. 前往 Sentry → Settings → API → Auth Tokens
2. 刪除舊的 Token
3. 建立新的 Token
4. 更新配置：`export-sentry-issue init`

### 錯誤：未提供 token

**原因：** 在命令列、環境變數或配置檔案中都找不到 token

**解決方法：**
- 執行 `export-sentry-issue init` 以儲存您的 token，或
- 使用 `--token` 參數，或
- 設定 `SENTRY_TOKEN` 環境變數

### 配置檔案權限不安全

**警告：** `Config file has insecure permissions!`

**原因：** 配置檔案可被其他使用者讀取

**解決方法：**
```bash
chmod 600 ~/.config/export-sentry-issue/config.json
```

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

# 使用已儲存的配置以提高安全性
export-sentry-issue export \
  --ids "$1" \
  --output "errors_$(date +%Y%m%d).txt"
```

使用方式：
```bash
# 首次：初始化配置
export-sentry-issue init

# 然後使用腳本
chmod +x export_today_errors.sh
./export_today_errors.sh "123,456,789"
```

### CI/CD 整合

對於自動化環境，使用環境變數：

```yaml
# GitHub Actions 範例
- name: Export Sentry Issues
  env:
    SENTRY_TOKEN: ${{ secrets.SENTRY_TOKEN }}
  run: |
    export-sentry-issue export \
      --base-url "https://sentry.io/api/0/projects/org/proj/issues/" \
      --ids "123,456" \
      --output "issues.txt"
```

## 常見問題

**Q: 可以匯出所有未解決的 issues 嗎？**

A: 此工具需要指定 Issue ID。要批次匯出，請先使用 Sentry API 列出所有 issues，然後提取 ID：

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

**Q: 我的 token 儲存在哪裡？**

A: 當您執行 `init` 時，token 會儲存在 `~/.config/export-sentry-issue/config.json`，檔案權限設定為 600（僅擁有者可讀寫）。

**Q: 使用 `init` 命令安全嗎？**

A: 是的。`init` 命令使用安全的實作方式：
- Token 輸入是隱藏的（使用 `getpass`）
- 檔案以嚴格的權限儲存（600）
- Token 會在儲存前驗證
- 如果檔案權限變得不安全會發出警告

**Q: 可以在 CI/CD pipeline 中使用嗎？**

A: 可以。對於 CI/CD，使用環境變數而非配置檔案：
```bash
export SENTRY_TOKEN="${{ secrets.SENTRY_TOKEN }}"
export-sentry-issue export --base-url "..." --ids "..."
```

## 授權

MIT License
