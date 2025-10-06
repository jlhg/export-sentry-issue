# Export Sentry Issue MCP Server

[English Version](README.md)

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) 伺服器，用於將 Sentry issues 匯出為純文字檔案。此伺服器提供工具讓 AI 助理（如 Claude）幫助您匯出和分析 Sentry 錯誤報告。

## 功能特色

- 🔧 **MCP 工具** 用於 Sentry issue 管理
- 🤖 **自動觸發** 當您提到 Sentry URL 或 issue 編號時
- 🔐 **安全配置** 檔案權限設為 600
- 📝 **豐富的匯出格式** 包含 stack traces、breadcrumbs、spans 和 context
- 🚀 **多種傳輸模式** (STDIO 和 HTTP/SSE)
- 🐳 **Docker 支援** 方便部署

## 安裝

**需求：** Python 3.10 或更高版本

### 從 PyPI 安裝（推薦）

```bash
pip install export-sentry-issue-mcp
```

### 從原始碼安裝

```bash
cd packages/export-sentry-issue-mcp
pip install -e .
```

## 使用方式

### 啟動伺服器

#### STDIO 模式（預設）

用於 Claude Desktop 或其他 MCP 客戶端：

```bash
export-sentry-issue-mcp
```

#### HTTP/SSE 模式

用於網頁整合：

```bash
export-sentry-issue-mcp --http --host 127.0.0.1 --port 3001
```

### Claude Code 配置（推薦）

#### 步驟 1: 建置 Docker Image

```bash
cd packages/export-sentry-issue-mcp
docker build -t export-sentry-issue-mcp:latest .
```

#### 步驟 2: 新增 MCP Server

```bash
claude mcp add export-sentry-issue -- docker run -i --rm export-sentry-issue-mcp:latest
```

#### 步驟 3: 驗證安裝

```bash
claude mcp list
```

您應該會在列表中看到 `export-sentry-issue`。

#### 步驟 4: （選用）持久化配置與儲存匯出檔案

若要保留 Sentry 配置並儲存匯出檔案：

```bash
claude mcp add export-sentry-issue -- docker run -i --rm \
  -v /path/to/your/config:/root/.config/export-sentry-issue \
  -v /path/to/your/output:/app \
  export-sentry-issue-mcp:latest
```

**注意：**
- 將 `/path/to/your/config` 替換為您的配置目錄（例如：`~/.config/export-sentry-issue`）
- 將 `/path/to/your/output` 替換為您想要的輸出目錄（例如：`~/sentry-exports`）
- 匯出的檔案會儲存在輸出目錄

### Claude Desktop 配置

若使用 Claude Desktop（非 Claude Code），請在 `claude_desktop_config.json` 中加入：

```json
{
  "mcpServers": {
    "export-sentry-issue": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/your/config:/root/.config/export-sentry-issue",
        "-v",
        "/path/to/your/output:/app",
        "export-sentry-issue-mcp:latest"
      ]
    }
  }
}
```

**注意：** 將 `/path/to/your/config` 和 `/path/to/your/output` 替換為實際路徑（例如：`${HOME}/.config/export-sentry-issue` 和 `${HOME}/sentry-exports`）。

## 可用工具

### 1. `view_sentry_issue`（自動觸發 🤖）

查看並匯出 Sentry issue(s) 的完整錯誤詳情。

**此工具會在以下情況自動觸發：**
- 您說「查看 Sentry issue #123」或「顯示 issue 123」
- 多個 issues：「查看 issues #123、#456、#789」或「issues 123 456 789」
- 提供 Sentry URL：「https://sentry.io/organizations/my-org/issues/12345/」
- 多個 URLs（空格或逗號分隔）
- 詢問「issue 123 的錯誤是什麼？」

**參數：**
- `issue_url_or_id`（必填）：Sentry issue URL(s) 或 ID(s)。支援：
  - 單一 ID：`"12345"`
  - 多個 IDs：`"12345, 67890, 11111"` 或 `"#123 #456 #789"`
  - 單一 URL：`"https://sentry.io/organizations/org/issues/123/"`
  - 多個 URLs：`"https://sentry.io/.../issues/123/ https://sentry.io/.../issues/456/"`
- `output_file`（選填）：自訂輸出檔名（預設：`sentry_issue(s)_TIMESTAMP.txt`）
- `debug`（選填）：啟用除錯模式（預設：`false`）

**使用範例：**
直接自然對話：
```
「請查看 Sentry issue #12345」
「顯示這個錯誤：https://sentry.io/organizations/my-org/issues/67890/」
「查看 issues #123、#456 和 #789」
「顯示這些錯誤：100 200 300」
```

**回傳：**

直接返回完整的 issue 內容，包含：
- 匯出摘要（成功/失敗數量）
- 完整錯誤訊息和 stack traces
- Breadcrumbs、spans 和 context 資料
- 儲存的檔案名稱

範例：
```
✅ 匯出完成！
成功：1
失敗：0
檔案已儲存：sentry_issue_12345_20251006_123456.txt

=== Issue Content ===
================================================================================
Issue ID: 12345
Title: TypeError: Cannot read property 'id' of undefined
...
[完整的 issue 詳細資訊，包含 stack traces、breadcrumbs 等]
```

檔案同時也會儲存到掛載的輸出目錄供後續參考。

### 2. `initialize_config`

初始化並儲存 Sentry 配置供未來使用。

**參數：**
- `base_url`（必填）：Sentry API base URL（例如：`https://sentry.io/api/0/projects/{org}/{project}/issues/`）
- `token`（必填）：Sentry Auth Token

**範例：**
```
「初始化我的 Sentry 配置，base_url 是 https://sentry.io/api/0/projects/my-org/my-project/issues/，token 是 sntrys_xxxxxxxxxxxxx」
```

**回傳：**
```
✅ 配置已成功儲存至：~/.config/export-sentry-issue/config.json
檔案權限：600（僅擁有者可讀寫）
```

### 3. `export_issues_tool`

將多個 Sentry issues 匯出為純文字檔案（批次匯出）。

**參數：**
- `issue_ids`（必填）：逗號分隔的 Issue ID（例如：`"12345,67890,11111"`）
- `base_url`（選填）：覆寫已儲存的 base URL
- `token`（選填）：覆寫已儲存的 token
- `output_file`（選填）：自訂輸出檔名（預設：`sentry_issues_TIMESTAMP.txt`）
- `debug`（選填）：啟用除錯模式以儲存原始 JSON 檔案（預設：`false`）

**範例：**
```
「匯出 Sentry issues 12345、67890 和 11111」
```

**回傳：**

直接返回完整的 issue 內容：
```
✅ 匯出完成！
成功：3
失敗：0
檔案已儲存：sentry_issues_20251006_123456.txt

=== Issue Content ===
[全部 3 個 issues 的完整內容，包含 stack traces、breadcrumbs 等]
```

檔案同時也會儲存到掛載的輸出目錄。

### 4. `list_config`

顯示目前已儲存的 Sentry 配置。

**參數：** 無

**範例：**
```
「顯示我的 Sentry 配置」
```

**回傳：**
```
配置檔案：~/.config/export-sentry-issue/config.json
Base URL: https://sentry.io/api/0/projects/my-org/my-project/issues/
Token: sntrys_xxxxxxxxxxxxx...
```

### 5. `revoke_config`

刪除已儲存的 Sentry 配置。

**參數：** 無

**範例：**
```
「撤銷我的 Sentry 配置」
```

**回傳：**
```
✅ 配置已從以下位置刪除：~/.config/export-sentry-issue/config.json

⚠️ 重要：請手動從 Sentry 撤銷 token：
  1. 前往：Settings → Account → API → Auth Tokens
  2. 找到並刪除該 token
```

## 匯出內容格式

匯出的文字檔案包含：

### 基本資訊
- Issue ID、標題、狀態、等級
- 發生次數
- 首次/最後發生時間
- 永久連結

### 詳細資訊
- **錯誤訊息**：例外類型和訊息
- **Stack Trace**：完整呼叫堆疊，包含：
  - 檔案路徑和行號
  - 函數名稱
  - 程式碼片段
  - 變數值
- **Request 資訊**：URL、Method、Query String、Headers
- **Breadcrumbs**：操作軌跡（包含資料庫查詢）
- **Spans**：效能追蹤與持續時間
- **使用者資訊**：使用者 ID、Email、IP
- **Context 資訊**：瀏覽器、作業系統、執行環境
- **Tags**：自訂標籤
- **額外資訊**：其他除錯資料

## Docker 使用

### 建置 Docker Image

```bash
cd packages/export-sentry-issue-mcp
docker build -t export-sentry-issue-mcp:latest .
```

### 使用 Docker 執行

```bash
docker run -it --rm export-sentry-issue-mcp:latest
```

### 掛載配置目錄執行

若要在執行間保留配置：

```bash
docker run -it --rm \
  -v ~/.config/export-sentry-issue:/root/.config/export-sentry-issue \
  export-sentry-issue-mcp:latest
```

## 取得必要資訊

### 1. 取得 Auth Token

1. 登入 Sentry
2. 導航至：**Settings** → **Account** → **API** → **Auth Tokens**
3. 點擊 **Create New Token**
4. 設定權限（最低需求）：
   - ✅ `event:read`
5. 複製產生的 Token

### 2. 取得 Base URL

**SaaS 版本：**
```
https://sentry.io/api/0/projects/{org-slug}/{project-slug}/issues/
```

**自架版本：**
```
https://your-sentry-domain.com/api/0/projects/{org-slug}/{project-slug}/issues/
```

**如何找到 org-slug 和 project-slug：**
- 在 Sentry UI 中，查看瀏覽器網址列
- 格式：`https://sentry.io/organizations/{org-slug}/projects/{project-slug}/`

### 3. 取得 Issue ID

- 在 Issue 詳細頁面，URL 結尾的數字就是 Issue ID
- 範例：`https://sentry.io/organizations/my-org/issues/12345/` → Issue ID 是 `12345`

## 安全考量

⚠️ **重要安全提醒：**

1. **配置檔案權限**：伺服器會自動將配置檔案權限設為 600（僅擁有者可讀寫）
2. **Token 儲存**：Tokens 儲存在本機 `~/.config/export-sentry-issue/config.json`
3. **無認證機制**：MCP 伺服器本身不支援認證 - 它以執行該伺服器的使用者權限執行
4. **敏感資料**：匯出的檔案可能包含：
   - 使用者 Email 和 IP 位址
   - Request Headers（Authorization 和 Cookie 已過濾）
   - 程式碼片段和變數值

   請安全地處理匯出的檔案。

## 除錯

### 使用 MCP Inspector

使用官方 inspector 除錯您的 MCP 伺服器：

```bash
npx @modelcontextprotocol/inspector export-sentry-issue-mcp
```

### 除錯模式

啟用除錯模式以儲存原始 JSON 回應：

```
「以除錯模式匯出 issue 12345」
```

這會建立 `debug_issue_12345.json` 檔案，包含完整的 API 回應。

## 疑難排解

### 錯誤：403 Forbidden

**原因：** Token 權限不足

**解決方法：**
1. 重新建立 Auth Token 並確保有 `event:read` 權限
2. 驗證您是專案的成員

### 錯誤：404 Not Found

**原因：** Base URL 或 Issue ID 不正確

**解決方法：**
1. 驗證 Base URL 格式
2. 檢查 Issue ID 在 Sentry UI 中是否存在
3. 驗證 org 和 project 名稱

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

## 開發

### 從原始碼執行

```bash
cd packages/export-sentry-issue-mcp
pip install -e .
export-sentry-issue-mcp
```

### 執行測試

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試（若可用）
pytest
```

## 授權

MIT License - 詳見 [LICENSE](../../LICENSE) 檔案

## 相關專案

- [export-sentry-issue](../../) - 獨立的 CLI 工具，用於匯出 Sentry issues
- [Model Context Protocol](https://modelcontextprotocol.io) - AI 工具整合的開放協定
- [FastMCP](https://github.com/jlowin/fastmcp) - 快速、Python 風格的 MCP 伺服器建置方式

## 支援

- 🐛 [回報問題](https://github.com/jlhg/export-sentry-issue/issues)
- 📖 [文件](https://github.com/jlhg/export-sentry-issue#readme)
