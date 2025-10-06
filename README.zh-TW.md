# Export Sentry Issue

[English Version](README.md)

匯出與分析 Sentry issues 的工具集合。

## 套件

此專案包含多個套件：

### 📦 [export-sentry-issue](packages/export-sentry-issue/)

匯出 Sentry issues 至純文字檔案的 Python CLI 工具。

**功能特色：**
- 匯出完整錯誤訊息與堆疊追蹤
- 支援自架 Sentry 及 SaaS 版本
- 包含請求資訊、Breadcrumbs、Spans 及上下文資料
- 具備檔案權限的安全 token 管理
- 批次匯出多個 issues

**快速開始：**
```bash
pip install export-sentry-issue

# 初始化設定（安全，token 隱藏）
export-sentry-issue init

# 匯出 issues
export-sentry-issue export --ids "12345,67890"
```

[📖 完整文件](packages/export-sentry-issue/README.zh-TW.md)

### 🔌 [export-sentry-issue-mcp](packages/export-sentry-issue-mcp/)

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) 伺服器，讓 Claude 等 AI 助理能匯出與分析 Sentry issues。

**功能特色：**
- 🔧 提供 MCP 工具管理 Sentry issue
- 🤖 提及 Sentry URL 或 issue 編號時自動觸發
- 🔐 具備檔案權限的安全設定
- 📝 豐富的匯出格式，包含堆疊追蹤、breadcrumbs、spans
- 🚀 支援多種傳輸模式（STDIO 和 HTTP/SSE）

**快速開始：**
```bash
pip install export-sentry-issue-mcp

# 初始化設定
export-sentry-issue-mcp init

# 加入到 Claude Desktop 設定 (~/.config/claude/claude_desktop_config.json)
{
  "mcpServers": {
    "sentry": {
      "command": "export-sentry-issue-mcp"
    }
  }
}
```

[📖 完整文件](packages/export-sentry-issue-mcp/README.zh-TW.md)

## 開發

此專案採用 monorepo 結構，包含多個 Python 套件。每個套件可獨立開發與發布。

### 專案結構

```
export-sentry-issue/
├── packages/
│   ├── export-sentry-issue/      # CLI 工具
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── export-sentry-issue-mcp/  # MCP 伺服器
│       ├── src/
│       ├── pyproject.toml
│       └── README.md
├── LICENSE
└── README.md
```

### 本地開發

```bash
# 以可編輯模式安裝套件
cd packages/export-sentry-issue
pip install -e .

# 或安裝 MCP 伺服器
cd packages/export-sentry-issue-mcp
pip install -e .
```

## 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案。
