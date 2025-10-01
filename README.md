# Sentry Issue Export Tool

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

- Python 3.6+
- `requests` library

### Setup

```bash
# Install dependencies
pip install requests

# Download the script
# Save the script as export_sentry_issue.py
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

### Basic Usage

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345,67890" \
  --token "your_sentry_token"
```

### Specify Output File

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345" \
  --token "your_token" \
  --output "critical_errors.txt"
```

### Debug Mode

When data is incomplete, use debug mode to inspect the raw data structure:

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.io/api/0/projects/my-org/my-project/issues/" \
  --ids "12345" \
  --token "your_token" \
  --debug
```

Debug mode will:
- Show available data fields
- Mark missing information
- Save raw JSON files (`debug_issue_{id}.json`)

## Parameters

| Parameter | Required | Description | Example |
|------|------|------|------|
| `--base-url` | ✅ | Sentry API base URL | `https://sentry.io/api/0/projects/org/proj/issues/` |
| `--ids` | ✅ | Issue ID list, comma-separated | `12345,67890,11111` |
| `--token` | ✅ | Sentry Auth Token | `sntrys_xxx...` |
| `--output` | ❌ | Output file name | `errors.txt` (default: `sentry_issues_TIMESTAMP.txt`) |
| `--debug` | ❌ | Enable debug mode | - |

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

### Example 1: Export Single Issue

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "issue_349.txt"
```

### Example 2: Batch Export Multiple Issues

```bash
python export_sentry_issue.py \
  --base-url "https://sentry.example.com/api/0/projects/my-org/web-app/issues/" \
  --ids "349,350,351,352,353" \
  --token "sntrys_xxxxxxxxxxxxx" \
  --output "batch_export.txt"
```

### Example 3: Self-hosted Sentry

```bash
python export_sentry_issue.py \
  --base-url "https://your-sentry-domain.com/api/0/projects/mycompany/backend/issues/" \
  --ids "100,101,102" \
  --token "your_token"
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
python export_sentry_issue.py --base-url "..." --ids "123" --token "..." --debug
```

Check `debug_issue_123.json` to see what data is actually available.

### Token Expired

**Solution:**
1. Go to Sentry → Settings → API → Auth Tokens
2. Delete old Token
3. Create new Token

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

python export_sentry_issue.py \
  --base-url "$SENTRY_BASE_URL" \
  --ids "$1" \
  --token "$SENTRY_TOKEN" \
  --output "errors_$(date +%Y%m%d).txt"
```

Usage:
```bash
chmod +x export_today_errors.sh
./export_today_errors.sh "123,456,789"
```

## FAQ

**Q: Can I export all unresolved issues?**

A: This script requires specific Issue IDs. To batch export, first list all issues using Sentry API, then extract IDs:

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

## License

MIT License
