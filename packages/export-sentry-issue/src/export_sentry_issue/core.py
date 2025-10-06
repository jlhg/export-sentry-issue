"""Core functionality for Sentry issue export."""

import json
import os
import requests
from datetime import datetime

from .config import parse_base_url


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
