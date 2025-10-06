# Sentry Issue Export Tool

[繁體中文版 (Traditional Chinese)](README.zh-TW.md)

Export Sentry issues to plain text files for offline analysis and debugging.

## Features

- Export complete error messages and stack traces
- Support both Self-hosted Sentry and SaaS version
- Include Request information, Breadcrumbs, and Context data
- Display code snippets and variable values
- Debug mode to inspect full data structure
- Batch export multiple issues

## Installation

### Requirements

- Python 3.10+
- `requests` library (automatically installed)

### Setup

```bash
pip install export-sentry-issue
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

## Usage

### Recommended: Secure Configuration

For better security, save your credentials to a configuration file instead of passing them on the command line:

```bash
# Step 1: Initialize (one-time setup)
export-sentry-issue init

# You'll be prompted to enter:
# - Base URL: https://sentry.io/api/0/projects/my-org/my-project/issues/
# - Token: (hidden input, won't appear on screen)

# Step 2: Export issues using saved configuration
export-sentry-issue export --ids "12345,67890"

# Step 3: When done, revoke and delete the configuration
export-sentry-issue revoke
```

The configuration is saved to `~/.config/export-sentry-issue/config.json` with secure permissions (600).

**✓ Security Benefits:**
- Token never appears in shell history
- Token never appears in process list
- Token stored with secure file permissions (owner read/write only)
- Easy to revoke when no longer needed

### Alternative: Command-Line Parameters

You can still provide credentials via command-line for CI/CD or one-time usage:

```bash
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890" \
  --token "your_sentry_token"
```

**⚠️ Security Warning:** Using `--token` on the command line may expose your token in:
- Shell history (e.g., `~/.bash_history`)
- Process list (visible to other users via `ps`)
- Log files and monitoring tools

### Alternative: Environment Variable

```bash
export SENTRY_TOKEN="your_sentry_token"
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890"
```

### Specify Output File

```bash
export-sentry-issue export \
  --ids "12345" \
  --output "critical_errors.txt"
```

### Debug Mode

When data is incomplete, use debug mode to inspect the raw data structure:

```bash
export-sentry-issue export \
  --ids "12345" \
  --debug
```

Debug mode will:
- Show available data fields
- Mark missing information
- Save raw JSON files (`debug_issue_{id}.json`)

## Commands

### `init` - Initialize Configuration

Securely save your Sentry credentials for future use.

```bash
export-sentry-issue init
```

**Features:**
- Interactive prompts for base URL and token
- Token input is hidden (not displayed on screen)
- Saves to `~/.config/export-sentry-issue/config.json`
- Sets secure file permissions (600 - owner read/write only)
- Verifies token validity before saving
- Allows overwriting existing configuration

### `export` - Export Issues

Export Sentry issues to a plain text file.

```bash
# Using saved configuration
export-sentry-issue export --ids "12345,67890"

# With custom output file
export-sentry-issue export --ids "12345" --output "errors.txt"

# Override saved configuration
export-sentry-issue export \
  --base-url "https://sentry.io/api/0/projects/org/proj/issues/" \
  --token "custom_token" \
  --ids "12345"
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--ids` | ✅ Yes | Issue ID list, comma-separated (e.g., `12345,67890,11111`) |
| `--base-url` | ❌ No* | Sentry API base URL |
| `--token` | ❌ No* | Sentry Auth Token |
| `--output` | ❌ No | Output file name (default: `sentry_issues_TIMESTAMP.txt`) |
| `--debug` | ❌ No | Enable debug mode, shows available fields and saves raw JSON |

*Required only if not configured via `init` command or environment variable

**Token Priority (highest to lowest):**
1. Command-line `--token` parameter
2. `SENTRY_TOKEN` environment variable
3. Saved configuration file (`~/.config/export-sentry-issue/config.json`)

### `revoke` - Revoke Token

Delete the saved configuration and get instructions to revoke the token from Sentry.

```bash
export-sentry-issue revoke
```

**Actions:**
- Displays current configuration details (masked token)
- Prompts for confirmation
- Deletes `~/.config/export-sentry-issue/config.json`
- Provides instructions to manually revoke token from Sentry UI

**Note:** You must manually revoke the token from Sentry:
1. Go to: **Settings** → **Account** → **API** → **Auth Tokens**
2. Find and delete the token

## Exported Content

The exported text file includes the following information:

### Basic Information
- Issue ID, Title, Status
- Occurrence count
- First/Last seen timestamps
- Permalink

### Detailed Information
- **Error Message**: Exception type and message
- **Stack Trace**: Complete call stack
  - File paths and line numbers
  - Function names
  - Code snippets
  - Variable values
- **Request Information**: URL, Method, Query String, Headers
- **Breadcrumbs**: Operation trail (including database queries)
- **User Information**: User ID, Email, IP
- **Context Information**: Browser, OS, Runtime
- **Tags**: Custom tags
- **Extra Information**: Additional debug data

## Examples

### Example 1: First Time Usage (Recommended)

```bash
# Initialize with your credentials
export-sentry-issue init
# Enter base URL: https://sentry.example.com/api/0/projects/my-org/web-app/issues/
# Enter token: (hidden input)

# Export a single issue
export-sentry-issue export --ids "349" --output "issue_349.txt"

# When done, clean up
export-sentry-issue revoke
```

### Example 2: Batch Export Multiple Issues

```bash
# Using saved configuration
export-sentry-issue export \
  --ids "349,350,351,352,353" \
  --output "batch_export.txt"
```

### Example 3: Self-hosted Sentry

```bash
# Initialize with self-hosted URL
export-sentry-issue init
# Enter base URL: https://your-sentry-domain.com/api/0/projects/mycompany/backend/issues/
# Enter token: (hidden input)

# Export issues
export-sentry-issue export --ids "100,101,102"
```

### Example 4: One-time Export (No Configuration)

```bash
# For CI/CD or one-time usage
export-sentry-issue export \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "issue_349.txt"
```

## Troubleshooting

### Error: 403 Forbidden

**Cause:** Insufficient token permissions

**Solution:**
1. Recreate Auth Token
2. Ensure the following permissions are checked:
   - `event:read`
3. Verify you are a member of the project

### Error: 404 Not Found

**Cause:** Incorrect Base URL or Issue ID

**Solution:**
1. Check if Base URL format is correct
2. Verify the Issue ID exists
3. Validate org and project names in Sentry UI

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

**Use debug mode to inspect:**
```bash
export-sentry-issue export --base-url "..." --ids "123" --token "..." --debug
```

Check `debug_issue_123.json` to see what data is actually available.

### Token Expired

**Solution:**
1. Go to Sentry → Settings → API → Auth Tokens
2. Delete old Token
3. Create new Token
4. Update configuration: `export-sentry-issue init`

### Error: No token provided

**Cause:** No token found in command-line, environment variable, or configuration file

**Solution:**
- Run `export-sentry-issue init` to save your token, OR
- Use `--token` parameter, OR
- Set `SENTRY_TOKEN` environment variable

### Configuration file has insecure permissions

**Warning:** `Config file has insecure permissions!`

**Cause:** Configuration file is readable by other users

**Solution:**
```bash
chmod 600 ~/.config/export-sentry-issue/config.json
```

## Advanced Usage

### Tracking N+1 Query Issues

To effectively track N+1 queries, enable database query tracing in your application:

**Django Example:**
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,  # Track all transactions
    send_default_pii=True,
)
```

Breadcrumbs will show each database query and its execution time.

### Performance Analysis

Enable Performance Monitoring for more detailed performance data:

```python
sentry_sdk.init(
    dsn="your-dsn",
    traces_sample_rate=1.0,  # 100% sampling
    profiles_sample_rate=1.0,  # Enable profiling
)
```

### Automation Script

Wrap common commands in a shell script:

```bash
#!/bin/bash
# export_today_errors.sh

# Use saved configuration for security
export-sentry-issue export \
  --ids "$1" \
  --output "errors_$(date +%Y%m%d).txt"
```

Usage:
```bash
# First time: initialize configuration
export-sentry-issue init

# Then use the script
chmod +x export_today_errors.sh
./export_today_errors.sh "123,456,789"
```

### CI/CD Integration

For automated environments, use environment variables:

```yaml
# GitHub Actions example
- name: Export Sentry Issues
  env:
    SENTRY_TOKEN: ${{ secrets.SENTRY_TOKEN }}
  run: |
    export-sentry-issue export \
      --base-url "https://sentry.io/api/0/projects/org/proj/issues/" \
      --ids "123,456" \
      --output "issues.txt"
```

## FAQ

**Q: Can I export all unresolved issues?**

A: This tool requires specific Issue IDs. To batch export, first list all issues using Sentry API, then extract IDs:

```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://sentry.io/api/0/projects/org/project/issues/?query=is:unresolved" \
  | jq '.[].id' | tr '\n' ','
```

**Q: Which Sentry versions are supported?**

A: Supports Sentry 9.0+ and all SaaS versions.

**Q: Will the exported data contain sensitive information?**

A: May include:
- User Email and IP addresses
- Request Headers (Authorization and Cookie are filtered)
- Code snippets and variable values

Please handle exported files securely.

**Q: Can I export to JSON or CSV?**

A: Currently only plain text format is supported. For JSON, use the debug mode generated JSON files.

**Q: Where is my token stored?**

A: When you run `init`, the token is stored in `~/.config/export-sentry-issue/config.json` with file permissions set to 600 (owner read/write only).

**Q: Is it safe to use the `init` command?**

A: Yes. The `init` command uses secure practices:
- Token input is hidden (uses `getpass`)
- File stored with restrictive permissions (600)
- Token is validated before saving
- Warns if file permissions become insecure

**Q: Can I use this in a CI/CD pipeline?**

A: Yes. For CI/CD, use environment variables instead of the config file:
```bash
export SENTRY_TOKEN="${{ secrets.SENTRY_TOKEN }}"
export-sentry-issue export --base-url "..." --ids "..."
```

## License

MIT License
