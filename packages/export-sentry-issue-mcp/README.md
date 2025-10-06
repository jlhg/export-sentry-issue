# Export Sentry Issue MCP Server

[繁體中文版 (Traditional Chinese)](README.zh-TW.md)

An [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for exporting Sentry issues to plain text files. This server provides tools that allow AI assistants like Claude to help you export and analyze Sentry error reports.

## Features

- 🔧 **MCP Tools** for Sentry issue management
- 🤖 **Auto-triggered** when you mention Sentry URLs or issue numbers
- 🔐 **Secure Configuration** with file permissions (600)
- 📝 **Rich Export Format** including stack traces, breadcrumbs, spans, and context
- 🚀 **Multiple Transport Modes** (STDIO and HTTP/SSE)
- 🐳 **Docker Support** for easy deployment

## Installation

**Requirements:** Python 3.10 or higher

### From PyPI (Recommended)

```bash
pip install export-sentry-issue-mcp
```

### From Source

```bash
cd packages/export-sentry-issue-mcp
pip install -e .
```

## Usage

### Running the Server

#### STDIO Mode (Default)

For use with Claude Desktop or other MCP clients:

```bash
export-sentry-issue-mcp
```

#### HTTP/SSE Mode

For web-based integration:

```bash
export-sentry-issue-mcp --http --host 127.0.0.1 --port 3001
```

### Claude Code Configuration (Recommended)

#### Step 1: Build Docker Image

```bash
cd packages/export-sentry-issue-mcp
docker build -t export-sentry-issue-mcp:latest .
```

#### Step 2: Add MCP Server

```bash
claude mcp add export-sentry-issue -- docker run -i --rm export-sentry-issue-mcp:latest
```

#### Step 3: Verify Installation

```bash
claude mcp list
```

You should see `export-sentry-issue` in the list.

#### Step 4: (Optional) Persist Configuration and Save Output Files

To keep your Sentry configuration and save exported files:

```bash
claude mcp add export-sentry-issue -- docker run -i --rm \
  -v /path/to/your/config:/root/.config/export-sentry-issue \
  -v /path/to/your/output:/app \
  export-sentry-issue-mcp:latest
```

**Note:**
- Replace `/path/to/your/config` with your config directory (e.g., `~/.config/export-sentry-issue`)
- Replace `/path/to/your/output` with your desired output directory (e.g., `~/sentry-exports`)
- Exported files will be saved to the output directory

### Claude Desktop Configuration

For Claude Desktop (not Claude Code), add to your `claude_desktop_config.json`:

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

**Note:** Replace `/path/to/your/config` and `/path/to/your/output` with your actual paths (e.g., `${HOME}/.config/export-sentry-issue` and `${HOME}/sentry-exports`).

## Available Tools

### 1. `view_sentry_issue` (Auto-triggered 🤖)

View and export Sentry issue(s) with complete error details.

**This tool is automatically triggered when you:**
- Say "Check Sentry issue #123" or "Show me issue 123"
- Multiple issues: "Check issues #123, #456, #789" or "issues 123 456 789"
- Provide a Sentry URL: "https://sentry.io/organizations/my-org/issues/12345/"
- Multiple URLs (space or comma separated)
- Ask "What's the error in issue 123?"

**Parameters:**
- `issue_url_or_id` (required): Sentry issue URL(s) or ID(s). Supports:
  - Single ID: `"12345"`
  - Multiple IDs: `"12345, 67890, 11111"` or `"#123 #456 #789"`
  - Single URL: `"https://sentry.io/organizations/org/issues/123/"`
  - Multiple URLs: `"https://sentry.io/.../issues/123/ https://sentry.io/.../issues/456/"`
- `output_file` (optional): Custom output filename (default: `sentry_issue(s)_TIMESTAMP.txt`)
- `debug` (optional): Enable debug mode (default: `false`)

**Example Usage:**
Just talk naturally:
```
"Please check Sentry issue #12345"
"Show me this error: https://sentry.io/organizations/my-org/issues/67890/"
"Check issues #123, #456, and #789"
"Show me these errors: 100 200 300"
```

**Returns:**

The complete issue content is returned directly, including:
- Export summary (success/failed counts)
- Full error messages and stack traces
- Breadcrumbs, spans, and context data
- Saved file name

Example:
```
✅ Export completed!
Success: 1
Failed: 0
File saved: sentry_issue_12345_20251006_123456.txt

=== Issue Content ===
================================================================================
Issue ID: 12345
Title: TypeError: Cannot read property 'id' of undefined
...
[Complete issue details including stack traces, breadcrumbs, etc.]
```

The file is also saved to the mounted output directory for later reference.

### 2. `initialize_config`

Initialize and save Sentry configuration for future use.

**Parameters:**
- `base_url` (required): Sentry API base URL (e.g., `https://sentry.io/api/0/projects/{org}/{project}/issues/`)
- `token` (required): Sentry Auth Token

**Example:**
```
"Initialize my Sentry config with base_url https://sentry.io/api/0/projects/my-org/my-project/issues/ and token sntrys_xxxxxxxxxxxxx"
```

**Returns:**
```
✅ Configuration saved successfully to: ~/.config/export-sentry-issue/config.json
File permissions: 600 (owner read/write only)
```

### 3. `export_issues_tool`

Export multiple Sentry issues to a plain text file (batch export).

**Parameters:**
- `issue_ids` (required): Comma-separated Issue IDs (e.g., `"12345,67890,11111"`)
- `base_url` (optional): Override saved base URL
- `token` (optional): Override saved token
- `output_file` (optional): Custom output filename (default: `sentry_issues_TIMESTAMP.txt`)
- `debug` (optional): Enable debug mode to save raw JSON files (default: `false`)

**Example:**
```
"Export Sentry issues 12345, 67890, and 11111"
```

**Returns:**

The complete issue content is returned directly:
```
✅ Export completed!
Success: 3
Failed: 0
File saved: sentry_issues_20251006_123456.txt

=== Issue Content ===
[Complete content of all 3 issues with stack traces, breadcrumbs, etc.]
```

The file is also saved to the mounted output directory.

### 4. `list_config`

Display the current saved Sentry configuration.

**Parameters:** None

**Example:**
```python
list_config()
```

**Returns:**
```
Configuration file: ~/.config/export-sentry-issue/config.json
Base URL: https://sentry.io/api/0/projects/my-org/my-project/issues/
Token: sntrys_xxxxxxxxxxxxx...
```

### 5. `revoke_config`

Delete the saved Sentry configuration.

**Parameters:** None

**Example:**
```python
revoke_config()
```

**Returns:**
```
✅ Configuration deleted from: ~/.config/export-sentry-issue/config.json

⚠️ IMPORTANT: Please manually revoke the token from Sentry:
  1. Go to: Settings → Account → API → Auth Tokens
  2. Find and delete the token
```

## Exported Content Format

The exported text file includes:

### Basic Information
- Issue ID, Title, Status, Level
- Occurrence count
- First/Last seen timestamps
- Permalink

### Detailed Information
- **Error Message**: Exception type and message
- **Stack Trace**: Complete call stack with:
  - File paths and line numbers
  - Function names
  - Code snippets
  - Variable values
- **Request Information**: URL, Method, Query String, Headers
- **Breadcrumbs**: Operation trail (including database queries)
- **Spans**: Performance traces with duration
- **User Information**: User ID, Email, IP
- **Context Information**: Browser, OS, Runtime
- **Tags**: Custom tags
- **Extra Information**: Additional debug data

## Docker Usage

### Build Docker Image

```bash
cd packages/export-sentry-issue-mcp
docker build -t export-sentry-issue-mcp:latest .
```

### Run with Docker

```bash
docker run -it --rm export-sentry-issue-mcp:latest
```

### Run with Configuration Mount

To persist configuration between runs:

```bash
docker run -it --rm \
  -v ~/.config/export-sentry-issue:/root/.config/export-sentry-issue \
  export-sentry-issue-mcp:latest
```

## Getting Required Information

### 1. Get Auth Token

1. Log in to Sentry
2. Navigate to: **Settings** → **Account** → **API** → **Auth Tokens**
3. Click **Create New Token**
4. Set permissions (minimum required):
   - ✅ `event:read`
5. Copy the generated Token

### 2. Get Base URL

**SaaS version:**
```
https://sentry.io/api/0/projects/{org-slug}/{project-slug}/issues/
```

**Self-hosted version:**
```
https://your-sentry-domain.com/api/0/projects/{org-slug}/{project-slug}/issues/
```

**How to find org-slug and project-slug:**
- In Sentry UI, check the browser address bar
- Format: `https://sentry.io/organizations/{org-slug}/projects/{project-slug}/`

### 3. Get Issue IDs

- On the Issue detail page, the number at the end of the URL is the Issue ID
- Example: `https://sentry.io/organizations/my-org/issues/12345/` → Issue ID is `12345`

## Security Considerations

⚠️ **Important Security Notes:**

1. **Configuration File Permissions**: The server automatically sets configuration file permissions to 600 (owner read/write only)
2. **Token Storage**: Tokens are stored locally in `~/.config/export-sentry-issue/config.json`
3. **No Authentication**: The MCP server itself does not support authentication - it runs with the privileges of the user running it
4. **Sensitive Data**: Exported files may contain:
   - User Email and IP addresses
   - Request Headers (Authorization and Cookie are filtered)
   - Code snippets and variable values

   Please handle exported files securely.

## Debugging

### Using MCP Inspector

Debug your MCP server with the official inspector:

```bash
npx @modelcontextprotocol/inspector export-sentry-issue-mcp
```

### Debug Mode

Enable debug mode to save raw JSON responses:

```python
export_issues(
    issue_ids="12345",
    debug=True
)
```

This will create `debug_issue_12345.json` files with complete API responses.

## Troubleshooting

### Error: 403 Forbidden

**Cause:** Insufficient token permissions

**Solution:**
1. Recreate Auth Token with `event:read` permission
2. Verify you are a member of the project

### Error: 404 Not Found

**Cause:** Incorrect Base URL or Issue ID

**Solution:**
1. Verify Base URL format
2. Check Issue ID exists in Sentry UI
3. Validate org and project names

### Missing Breadcrumbs or Request Information

**Cause:** Sentry SDK features not enabled

**Solution:**

Enable `send_default_pii` in your application:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-dsn",
    send_default_pii=True,  # Enable Request and User information
    traces_sample_rate=1.0,  # Enable performance tracing
)
```

## Development

### Running from Source

```bash
cd packages/export-sentry-issue-mcp
pip install -e .
export-sentry-issue-mcp
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest
```

## License

MIT License - See [LICENSE](../../LICENSE) file for details

## Related Projects

- [export-sentry-issue](../../) - Standalone CLI tool for exporting Sentry issues
- [Model Context Protocol](https://modelcontextprotocol.io) - Open protocol for AI tool integration
- [FastMCP](https://github.com/jlowin/fastmcp) - Fast, Pythonic way to build MCP servers

## Support

- 🐛 [Report Issues](https://github.com/jlhg/export-sentry-issue/issues)
- 📖 [Documentation](https://github.com/jlhg/export-sentry-issue#readme)
