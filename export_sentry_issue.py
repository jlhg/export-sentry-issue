#!/usr/bin/env python3

import requests
import argparse
from datetime import datetime
import re
import os
import json
import sys
import getpass
from pathlib import Path
import stat

CONFIG_DIR = Path.home() / ".config" / "export-sentry-issue"
CONFIG_FILE = CONFIG_DIR / "config.json"

def parse_base_url(base_url):
    """Parse API base URL from the provided base_url"""
    # Extract https://sentry.io/api/0 part
    match = re.match(r'(https?://[^/]+/api/\d+)', base_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid base_url format")

def ensure_config_dir():
    """Ensure config directory exists with proper permissions"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to 700 (owner read/write/execute only)
    os.chmod(CONFIG_DIR, stat.S_IRWXU)

def save_config(base_url, token):
    """Save configuration to file with secure permissions"""
    ensure_config_dir()

    config = {
        "base_url": base_url,
        "token": token
    }

    # Write config file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    # Set file permissions to 600 (owner read/write only)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)

def load_config():
    """Load configuration from file"""
    if not CONFIG_FILE.exists():
        return None

    # Check file permissions
    file_stat = os.stat(CONFIG_FILE)
    if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
        print("⚠️  Warning: Config file has insecure permissions!")
        print(f"   Please run: chmod 600 {CONFIG_FILE}")

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def delete_config():
    """Delete configuration file"""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        return True
    return False

def get_issue_details(base_api_url, token, issue_id):
    """Get complete details of a single issue"""
    url = f"{base_api_url}/issues/{issue_id}/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_latest_event(base_api_url, token, issue_id):
    """Get the latest event with complete data for the issue"""
    url = f"{base_api_url}/issues/{issue_id}/events/latest/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_issue_events(base_api_url, token, issue_id):
    """Get list of events for the issue"""
    url = f"{base_api_url}/issues/{issue_id}/events/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def save_debug_json(data, filename):
    """Save raw JSON for debugging purposes"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_issue_to_text(issue, latest_event, debug_mode=False):
    """Format issue data into readable plain text"""
    output = []

    # Basic information
    output.append("=" * 80)
    output.append(f"Issue ID: {issue['id']}")
    output.append(f"Title: {issue['title']}")
    output.append(f"Status: {issue['status']}")
    output.append(f"Level: {issue['level']}")
    output.append(f"Count: {issue['count']}")
    output.append(f"First Seen: {issue['firstSeen']}")
    output.append(f"Last Seen: {issue['lastSeen']}")
    output.append(f"Permalink: {issue['permalink']}")
    output.append("=" * 80)
    output.append("")

    # Error message
    if issue.get('metadata'):
        output.append("【Error Message】")
        output.append(issue['metadata'].get('value', 'N/A'))
        if issue['metadata'].get('type'):
            output.append(f"Type: {issue['metadata']['type']}")
        output.append("")

    # Debug mode: show available fields
    if debug_mode and latest_event:
        output.append("【DEBUG: Available Fields】")
        output.append(f"Event top-level fields: {', '.join(latest_event.keys())}")
        if 'entries' in latest_event:
            output.append(f"Entry types: {[e.get('type') for e in latest_event['entries']]}")
        output.append("")

    if not latest_event:
        output.append("⚠️  Unable to retrieve event details")
        return "\n".join(output)

    # Event ID and timestamp
    output.append("【Event Information】")
    if latest_event.get('eventID'):
        output.append(f"Event ID: {latest_event['eventID']}")
    if latest_event.get('dateCreated'):
        output.append(f"Occurred at: {latest_event['dateCreated']}")
    output.append("")

    # User information
    if latest_event.get('user'):
        output.append("【User Information】")
        user = latest_event['user']
        if user.get('id'):
            output.append(f"  ID: {user['id']}")
        if user.get('email'):
            output.append(f"  Email: {user['email']}")
        if user.get('username'):
            output.append(f"  Username: {user['username']}")
        if user.get('ip_address'):
            output.append(f"  IP: {user['ip_address']}")
        output.append("")

    # Request information
    if latest_event.get('request'):
        output.append("【Request Information】")
        req = latest_event['request']
        if req.get('url'):
            output.append(f"  URL: {req['url']}")
        if req.get('method'):
            output.append(f"  Method: {req['method']}")
        if req.get('query_string'):
            output.append(f"  Query String: {req['query_string']}")
        if req.get('data'):
            output.append(f"  Request Data: {req['data']}")
        if req.get('headers'):
            output.append("  Headers:")
            for key, value in req['headers'].items():
                if key.lower() not in ['authorization', 'cookie', 'set-cookie']:
                    output.append(f"    {key}: {value}")
        output.append("")
    elif debug_mode:
        output.append("⚠️  Request information not found")
        output.append("")

    # Breadcrumbs
    breadcrumbs_found = False
    if latest_event.get('entries'):
        for entry in latest_event['entries']:
            if entry['type'] == 'breadcrumbs':
                breadcrumbs_found = True
                output.append("【Breadcrumbs】")
                breadcrumbs = entry['data'].get('values', [])

                if not breadcrumbs:
                    output.append("  (No breadcrumbs data)")
                else:
                    # Show all breadcrumbs
                    for bc in breadcrumbs:
                        timestamp = bc.get('timestamp', 'N/A')
                        category = bc.get('category', 'N/A')
                        message = bc.get('message', '')
                        level = bc.get('level', 'info')
                        bc_type = bc.get('type', 'default')

                        output.append(f"  [{timestamp}] [{level}] [{category}] {bc_type}")
                        if message:
                            output.append(f"    Message: {message}")

                        # Show data (may include queries, duration, etc.)
                        if bc.get('data'):
                            data = bc['data']
                            for key, value in data.items():
                                if key == 'query':
                                    output.append(f"    Query: {value}")
                                elif key == 'duration':
                                    output.append(f"    Duration: {value}ms")
                                else:
                                    output.append(f"    {key}: {value}")
                        output.append("")
                break

    if not breadcrumbs_found and debug_mode:
        output.append("⚠️  Breadcrumbs not found")
        output.append("")

    # Spans (performance traces)
    spans_found = False
    if latest_event.get('entries'):
        for entry in latest_event['entries']:
            if entry['type'] == 'spans':
                spans_found = True
                output.append("【Spans (Performance Traces)】")
                spans = entry.get('data', [])

                if not spans:
                    output.append("  (No spans data)")
                else:
                    # Show all spans with duration
                    for span in spans:
                        span_id = span.get('span_id', 'N/A')
                        op = span.get('op', 'N/A')
                        description = span.get('description', '')
                        status = span.get('status', 'unknown')

                        # Calculate duration from timestamps
                        start_ts = span.get('start_timestamp')
                        end_ts = span.get('timestamp')
                        duration_ms = None
                        if start_ts and end_ts:
                            duration_ms = (end_ts - start_ts) * 1000  # Convert to milliseconds

                        # Also check for exclusive_time (actual execution time excluding child spans)
                        exclusive_time = span.get('exclusive_time')

                        output.append(f"  Span ID: {span_id}")
                        output.append(f"    Operation: {op}")
                        output.append(f"    Status: {status}")

                        if duration_ms is not None:
                            output.append(f"    Duration: {duration_ms:.3f}ms")
                        if exclusive_time is not None:
                            output.append(f"    Exclusive Time: {exclusive_time:.3f}ms")

                        if description:
                            # Truncate long descriptions
                            if len(description) > 200:
                                description = description[:200] + "..."
                            output.append(f"    Description: {description}")

                        # Show parent span if exists
                        if span.get('parent_span_id'):
                            output.append(f"    Parent Span: {span['parent_span_id']}")

                        # Show additional data
                        if span.get('data'):
                            data = span['data']
                            output.append(f"    Data:")
                            for key, value in data.items():
                                str_value = str(value)
                                if len(str_value) > 100:
                                    str_value = str_value[:100] + "..."
                                output.append(f"      {key}: {str_value}")

                        output.append("")
                break

    if not spans_found and debug_mode:
        output.append("⚠️  Spans not found")
        output.append("")

    # Stack trace
    output.append("【Stack Trace】")
    if latest_event.get('entries'):
        for entry in latest_event['entries']:
            if entry['type'] == 'exception':
                exceptions = entry['data'].get('values', [])
                for exc in exceptions:
                    output.append(f"\nException Type: {exc.get('type', 'Unknown')}")
                    output.append(f"Exception Message: {exc.get('value', 'N/A')}")

                    if exc.get('mechanism'):
                        output.append(f"Mechanism: {exc['mechanism'].get('type', 'N/A')}")

                    if exc.get('stacktrace'):
                        output.append("\nCall Stack:")
                        frames = exc['stacktrace'].get('frames', [])
                        for frame in reversed(frames):
                            filename = frame.get('filename', 'unknown')
                            function = frame.get('function', 'unknown')
                            lineno = frame.get('lineNo', '?')
                            in_app = frame.get('inApp', False)

                            app_marker = "[APP] " if in_app else ""
                            output.append(f"  {app_marker}File: {filename}:{lineno}")
                            output.append(f"  Function: {function}")

                            # Show variables
                            if frame.get('vars'):
                                output.append("  Variables:")
                                for var_name, var_value in frame['vars'].items():
                                    # Truncate long values
                                    str_value = str(var_value)
                                    if len(str_value) > 200:
                                        str_value = str_value[:200] + "..."
                                    output.append(f"    {var_name} = {str_value}")

                            # Code snippet
                            if frame.get('context'):
                                output.append("  Code:")
                                for line in frame['context']:
                                    line_no, code = line[0], line[1]
                                    marker = ">>> " if line_no == lineno else "    "
                                    output.append(f"  {marker}{line_no}: {code}")
                            output.append("")

    # Tags
    if latest_event.get('tags'):
        output.append("【Tags】")
        for tag in latest_event['tags']:
            output.append(f"  {tag['key']}: {tag['value']}")
        output.append("")

    # Environment/Context information
    if latest_event.get('contexts'):
        output.append("【Context Information】")
        contexts = latest_event['contexts']

        for context_name, context_data in contexts.items():
            if not isinstance(context_data, dict):
                continue

            if context_name == 'runtime':
                output.append(f"  Runtime: {context_data.get('name')} {context_data.get('version')}")
            elif context_name == 'browser':
                output.append(f"  Browser: {context_data.get('name')} {context_data.get('version')}")
            elif context_name == 'os':
                output.append(f"  OS: {context_data.get('name')} {context_data.get('version')}")
            elif context_name == 'device':
                output.append(f"  Device: {context_data.get('model', 'N/A')}")
            else:
                # Custom context
                output.append(f"  {context_name}:")
                for k, v in context_data.items():
                    if k != 'type':  # Skip type field
                        output.append(f"    {k}: {v}")
        output.append("")

    # Extra information
    if latest_event.get('extra'):
        output.append("【Extra Information】")
        for key, value in latest_event['extra'].items():
            str_value = str(value)
            if len(str_value) > 500:
                str_value = str_value[:500] + "..."
            output.append(f"  {key}: {str_value}")
        output.append("")

    # SDK information
    if latest_event.get('sdk'):
        output.append("【SDK Information】")
        sdk = latest_event['sdk']
        output.append(f"  Name: {sdk.get('name', 'N/A')}")
        output.append(f"  Version: {sdk.get('version', 'N/A')}")
        output.append("")

    return "\n".join(output)

def get_api_tokens(base_api_url, token):
    """Get list of API tokens"""
    url = f"{base_api_url.rsplit('/api/', 1)[0]}/api/0/api-tokens/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def revoke_token(base_api_url, token):
    """Revoke the current API token"""
    try:
        # Get token info to find the token ID
        tokens = get_api_tokens(base_api_url, token)

        # Find current token by comparing the token value (Sentry API limitations)
        # Since we can't directly identify which token ID corresponds to our token,
        # we'll just inform the user to manually revoke it from the UI
        print("Note: Automatic token revocation requires the token ID.")
        print("Please revoke the token manually from Sentry:")
        print("  Settings → Account → API → Auth Tokens")
        return False

    except Exception as e:
        print(f"Error: Unable to revoke token automatically: {e}")
        print("Please revoke the token manually from Sentry:")
        print("  Settings → Account → API → Auth Tokens")
        return False

def cmd_init(args):
    """Initialize configuration by prompting for credentials"""
    print("=== Sentry Issue Export Tool - Initialization ===\n")

    # Check if config already exists
    if CONFIG_FILE.exists():
        print(f"⚠️  Configuration already exists at: {CONFIG_FILE}")
        response = input("Do you want to overwrite it? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Initialization cancelled.")
            return

    # Get base URL
    print("\nEnter your Sentry API base URL")
    print("Format: https://sentry.io/api/0/projects/{org}/{project}/issues/")
    print("Or: https://your-domain.com/api/0/projects/{org}/{project}/issues/")
    base_url = input("\nBase URL: ").strip()

    if not base_url:
        print("Error: Base URL is required")
        sys.exit(1)

    try:
        parsed_url = parse_base_url(base_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get token securely
    print("\nEnter your Sentry Auth Token")
    print("(Get it from: Settings → Account → API → Auth Tokens)")
    token = getpass.getpass("Token (hidden): ").strip()

    if not token:
        print("Error: Token is required")
        sys.exit(1)

    # Verify token by making a test API call
    print("\nVerifying token...")
    try:
        # Test with the actual issues endpoint that requires event:read permission
        # This is what the script will actually use, so it's the best validation
        headers = {"Authorization": f"Bearer {token}"}
        # Try to list issues (this requires event:read permission)
        response = requests.get(base_url, headers=headers)

        # Check for authentication/permission errors
        if response.status_code == 401:
            raise requests.exceptions.HTTPError("401 Unauthorized - Invalid token")
        elif response.status_code == 403:
            raise requests.exceptions.HTTPError("403 Forbidden - Token lacks required permissions (event:read)")

        # If we get 200 or even 404 (project not found but auth is ok), token is valid
        response.raise_for_status()
        print("✓ Token verified successfully")
    except requests.exceptions.RequestException as e:
        print(f"✗ Token verification failed: {e}")
        response = input("\nSave anyway? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Initialization cancelled.")
            sys.exit(1)

    # Save configuration
    save_config(base_url, token)
    print(f"\n✓ Configuration saved to: {CONFIG_FILE}")
    print(f"  File permissions: 600 (owner read/write only)")
    print("\nYou can now use the export command without specifying --token:")
    print(f"  {sys.argv[0]} export --ids \"12345,67890\"")

def cmd_revoke(args):
    """Revoke token and delete configuration"""
    print("=== Revoke Sentry Token ===\n")

    config = load_config()
    if not config:
        print(f"Error: No configuration found at {CONFIG_FILE}")
        print("Nothing to revoke.")
        sys.exit(1)

    print(f"Configuration file: {CONFIG_FILE}")
    print(f"Base URL: {config.get('base_url', 'N/A')}")
    print(f"Token: {config.get('token', '')[:20]}..." if config.get('token') else "Token: N/A")

    response = input("\nAre you sure you want to revoke and delete this configuration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    # Try to revoke token via API
    try:
        base_api_url = parse_base_url(config['base_url'])
        revoke_token(base_api_url, config['token'])
    except Exception as e:
        print(f"Warning: Could not revoke token via API: {e}")

    # Delete config file
    if delete_config():
        print(f"\n✓ Configuration deleted from: {CONFIG_FILE}")
        print("\nIMPORTANT: Please manually revoke the token from Sentry:")
        print("  1. Go to: Settings → Account → API → Auth Tokens")
        print("  2. Find and delete the token")
    else:
        print("Error: Could not delete configuration file")

def cmd_export(args):
    """Export issues (original functionality)"""
    # Get token from args, environment, or config file
    token = args.token

    if not token:
        token = os.environ.get('SENTRY_TOKEN')

    if not token:
        config = load_config()
        if config:
            token = config.get('token')
            # Also use base_url from config if not provided
            if not args.base_url:
                args.base_url = config.get('base_url')

    if not token:
        print("Error: No token provided.")
        print("Please either:")
        print(f"  1. Run '{sys.argv[0]} init' to save your token")
        print("  2. Use --token parameter")
        print("  3. Set SENTRY_TOKEN environment variable")
        sys.exit(1)

    if not args.base_url:
        print("Error: No base URL provided.")
        print("Please either:")
        print(f"  1. Run '{sys.argv[0]} init' to save your configuration")
        print("  2. Use --base-url parameter")
        sys.exit(1)

    issue_ids = [id.strip() for id in args.ids.split(',') if id.strip()]

    if not issue_ids:
        print("Error: No valid Issue IDs provided")
        sys.exit(1)

    print(f"Preparing to export {len(issue_ids)} issue(s)...")
    if args.debug:
        print("🔍 Debug mode enabled")

    export_issues(args.base_url, token, issue_ids, args.output, args.debug)

def export_issues(base_url, token, issue_ids, output_file=None, debug_mode=False):
    """Export specified issues to a single file"""
    base_api_url = parse_base_url(base_url)

    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sentry_issues_{timestamp}.txt"

    success_count = 0
    failed_count = 0

    with open(output_file, "w", encoding="utf-8") as f:
        for i, issue_id in enumerate(issue_ids, 1):
            try:
                print(f"Processing {i}/{len(issue_ids)}: Issue ID {issue_id}")

                # Get detailed information
                issue_detail = get_issue_details(base_api_url, token, issue_id)

                # Try to get complete data for the latest event
                try:
                    latest_event = get_latest_event(base_api_url, token, issue_id)
                except:
                    # If failed, try to get from event list
                    events = get_issue_events(base_api_url, token, issue_id)
                    latest_event = events[0] if events else None

                # Debug mode: save raw JSON
                if debug_mode and latest_event:
                    debug_file = f"debug_issue_{issue_id}.json"
                    save_debug_json(latest_event, debug_file)
                    print(f"  Debug JSON saved: {debug_file}")

                # Format and write
                text = format_issue_to_text(issue_detail, latest_event, debug_mode)
                f.write(text)
                f.write("\n\n" + "="*80 + "\n\n")

                success_count += 1

            except Exception as e:
                error_msg = f"Error processing Issue {issue_id}: {str(e)}"
                print(f"  ✗ {error_msg}")
                f.write(f"\nError: {error_msg}\n\n")
                failed_count += 1

    print("\n" + "=" * 80)
    print(f"Export completed!")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Output file: {os.path.abspath(output_file)}")

def main():
    parser = argparse.ArgumentParser(
        description='Export Sentry issues to plain text file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Initialize (first time setup)
  python export_sentry_issue.py init

  # Export issues (using saved configuration)
  python export_sentry_issue.py export --ids "12345,67890"

  # Export issues (with explicit token)
  python export_sentry_issue.py export --base-url "https://sentry.example.com/api/0/projects/my-org/my-project/issues/" --ids "12345,67890" --token "your_token"

  # Revoke token and delete configuration
  python export_sentry_issue.py revoke
        '''
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # Init command
    parser_init = subparsers.add_parser('init', help='Initialize configuration')
    parser_init.set_defaults(func=cmd_init)

    # Export command
    parser_export = subparsers.add_parser('export', help='Export Sentry issues')
    parser_export.add_argument(
        '--base-url',
        help='Sentry API base URL (optional if already configured)'
    )
    parser_export.add_argument(
        '--ids',
        required=True,
        help='Issue IDs to export, comma-separated, e.g.: 12345,67890,11111'
    )
    parser_export.add_argument(
        '--token',
        help='Sentry Auth Token (optional if already configured)'
    )
    parser_export.add_argument(
        '--output',
        help='Output file name (optional, default: sentry_issues_TIMESTAMP.txt)'
    )
    parser_export.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode, shows available fields and saves raw JSON'
    )
    parser_export.set_defaults(func=cmd_export)

    # Revoke command
    parser_revoke = subparsers.add_parser('revoke', help='Revoke token and delete configuration')
    parser_revoke.set_defaults(func=cmd_revoke)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
