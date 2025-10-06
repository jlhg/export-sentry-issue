# Export Sentry Issue

[繁體中文版 (Traditional Chinese)](README.zh-TW.md)

A collection of tools for exporting and analyzing Sentry issues.

## Packages

This repository contains multiple packages:

### 📦 [export-sentry-issue](packages/export-sentry-issue/)

A Python CLI tool for exporting Sentry issues to plain text files.

**Features:**
- Export complete error messages and stack traces
- Support both Self-hosted Sentry and SaaS version
- Include Request information, Breadcrumbs, Spans, and Context data
- Secure token management with file permissions
- Batch export multiple issues

**Quick Start:**
```bash
pip install export-sentry-issue

# Initialize configuration (secure, token hidden)
export-sentry-issue init

# Export issues
export-sentry-issue export --ids "12345,67890"
```

[📖 Full Documentation](packages/export-sentry-issue/README.md)

### 🔌 [export-sentry-issue-mcp](packages/export-sentry-issue-mcp/)

An [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that allows AI assistants like Claude to export and analyze Sentry issues.

**Features:**
- 🔧 MCP Tools for Sentry issue management
- 🤖 Auto-triggered when you mention Sentry URLs or issue numbers
- 🔐 Secure configuration with file permissions
- 📝 Rich export format with stack traces, breadcrumbs, spans
- 🚀 Multiple transport modes (STDIO and HTTP/SSE)

**Quick Start:**
```bash
pip install export-sentry-issue-mcp

# Initialize configuration
export-sentry-issue-mcp init

# Add to Claude Desktop config (~/.config/claude/claude_desktop_config.json)
{
  "mcpServers": {
    "sentry": {
      "command": "export-sentry-issue-mcp"
    }
  }
}
```

[📖 Full Documentation](packages/export-sentry-issue-mcp/README.md)

## Development

This is a monorepo containing multiple Python packages. Each package can be developed and published independently.

### Project Structure

```
export-sentry-issue/
├── packages/
│   ├── export-sentry-issue/      # CLI tool
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── export-sentry-issue-mcp/  # MCP server
│       ├── src/
│       ├── pyproject.toml
│       └── README.md
├── LICENSE
└── README.md
```

### Local Development

```bash
# Install a package in editable mode
cd packages/export-sentry-issue
pip install -e .

# Or for the MCP server
cd packages/export-sentry-issue-mcp
pip install -e .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
