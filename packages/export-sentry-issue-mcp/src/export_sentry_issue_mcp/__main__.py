#!/usr/bin/env python3
"""Export Sentry Issue MCP Server

An MCP server that provides tools to export Sentry issues to plain text files.
"""

import argparse
import os
import re
from datetime import datetime
from typing import Annotated

import requests
from fastmcp import FastMCP
from pydantic import Field

# Import from export-sentry-issue base package
from export_sentry_issue import (
    CONFIG_FILE,
    parse_base_url,
    save_config,
    load_config,
    delete_config,
    get_issue_details,
    get_latest_event,
    get_issue_events,
    save_debug_json,
    format_issue_to_text,
)

# Initialize FastMCP server
mcp = FastMCP("Export Sentry Issue MCP Server")


def load_config_safe():
    """Load config with MCP-specific error handling for insecure permissions"""
    import stat

    if not CONFIG_FILE.exists():
        return None

    # Check file permissions
    file_stat = os.stat(CONFIG_FILE)
    if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
        return {
            "error": "Config file has insecure permissions",
            "suggestion": f"Run: chmod 600 {CONFIG_FILE}"
        }

    return load_config()


def export_issues_impl(base_url: str, token: str, issue_ids: list[str], output_file: str | None = None, debug_mode: bool = False) -> dict:
    """Export specified issues to a single file"""
    base_api_url = parse_base_url(base_url)

    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sentry_issues_{timestamp}.txt"

    # Get output directory from environment (for Docker volume mapping)
    output_dir = os.environ.get('OUTPUT_DIR', '/app')
    if not os.path.isabs(output_file):
        container_output_file = os.path.join(output_dir, output_file)
    else:
        container_output_file = output_file

    success_count = 0
    failed_count = 0

    with open(container_output_file, "w", encoding="utf-8") as f:
        for i, issue_id in enumerate(issue_ids, 1):
            try:
                issue_detail = get_issue_details(base_api_url, token, issue_id)

                try:
                    latest_event = get_latest_event(base_api_url, token, issue_id)
                except:
                    events = get_issue_events(base_api_url, token, issue_id)
                    latest_event = events[0] if events else None

                if debug_mode and latest_event:
                    debug_file = f"debug_issue_{issue_id}.json"
                    save_debug_json(latest_event, debug_file)

                text = format_issue_to_text(issue_detail, latest_event, debug_mode)
                f.write(text)
                f.write("\n\n" + "="*80 + "\n\n")

                success_count += 1

            except Exception as e:
                error_msg = f"Error processing Issue {issue_id}: {str(e)}"
                f.write(f"\nError: {error_msg}\n\n")
                failed_count += 1

    # Map container path to host path for Docker volumes
    host_output_dir = os.environ.get('HOST_OUTPUT_DIR')
    if host_output_dir and output_dir:
        # Replace container path prefix with host path prefix
        final_path = container_output_file.replace(output_dir, host_output_dir, 1)
    else:
        final_path = os.path.abspath(container_output_file)

    return {
        "success": success_count,
        "failed": failed_count,
        "output_file": final_path
    }


# MCP Tools
@mcp.tool()
def initialize_config(
    base_url: Annotated[str, Field(description="Sentry API base URL (e.g., https://sentry.io/api/0/projects/{org}/{project}/issues/)")],
    token: Annotated[str, Field(description="Sentry Auth Token")]
) -> str:
    """Initialize and save Sentry configuration to ~/.config/export-sentry-issue/config.json

    This tool securely stores your Sentry credentials for future use.
    The configuration file is created with secure permissions (600 - owner read/write only).
    """
    try:
        # Verify token by making a test API call
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(base_url, headers=headers)

        if response.status_code == 401:
            return "❌ Error: Invalid token (401 Unauthorized)"
        elif response.status_code == 403:
            return "❌ Error: Token lacks required permissions (403 Forbidden). Ensure 'event:read' permission is enabled."

        response.raise_for_status()

        # Save configuration
        save_config(base_url, token)

        return f"✅ Configuration saved successfully to: {CONFIG_FILE}\nFile permissions: 600 (owner read/write only)"

    except requests.exceptions.RequestException as e:
        return f"⚠️ Warning: Token verification failed: {e}\nConfiguration was NOT saved."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _do_export_issues(
    issue_ids: str,
    base_url: str | None = None,
    token: str | None = None,
    output_file: str | None = None,
    debug: bool = False
) -> str:
    """Internal function to handle the actual export logic."""
    try:
        # Get token from environment or config if not provided
        actual_token = token
        actual_base_url = base_url

        if not actual_token:
            actual_token = os.environ.get('SENTRY_TOKEN')

        if not actual_token or not actual_base_url:
            config = load_config_safe()
            if config:
                if "error" in config:
                    return f"❌ {config['error']}\n{config['suggestion']}"

                if not actual_token:
                    actual_token = config.get('token')
                if not actual_base_url:
                    actual_base_url = config.get('base_url')

        if not actual_token:
            return "❌ Error: No token provided.\nPlease either:\n  1. Use 'initialize_config' tool to save your token\n  2. Provide 'token' parameter\n  3. Set SENTRY_TOKEN environment variable"

        if not actual_base_url:
            return "❌ Error: No base URL provided.\nPlease either:\n  1. Use 'initialize_config' tool to save your configuration\n  2. Provide 'base_url' parameter"

        # Parse issue IDs
        ids_list = [id.strip() for id in issue_ids.split(',') if id.strip()]

        if not ids_list:
            return "❌ Error: No valid Issue IDs provided"

        # Export issues
        result = export_issues_impl(actual_base_url, actual_token, ids_list, output_file, debug)

        # Read the file content to return to user
        with open(result['output_file'], 'r', encoding='utf-8') as f:
            content = f.read()

        # Return complete content with summary
        output_msg = f"✅ Export completed!\n"
        output_msg += f"Success: {result['success']}\n"
        output_msg += f"Failed: {result['failed']}\n"
        output_msg += f"File saved: {os.path.basename(result['output_file'])}\n\n"
        output_msg += "=== Issue Content ===\n"
        output_msg += content

        return output_msg

    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def view_sentry_issue(
    issue_url_or_id: Annotated[str, Field(description="Sentry issue URL(s) or ID(s). Supports: single ID '12345', multiple IDs '12345, 67890, 11111', single URL, or multiple URLs separated by commas or spaces")],
    output_file: Annotated[str | None, Field(description="Output file name (optional, defaults to sentry_issue(s)_TIMESTAMP.txt)")] = None,
    debug: Annotated[bool, Field(description="Enable debug mode to save raw JSON files")] = False
) -> str:
    """View and export Sentry issue(s) with complete error details.

    **Use this tool when the user mentions:**
    - "Check/view/show Sentry issue #123" or "Sentry issue 123"
    - "Check issues #123, #456, #789" or "issues 123, 456, 789"
    - A Sentry URL like "https://sentry.io/organizations/org/issues/123/"
    - Multiple URLs: "https://sentry.io/.../issues/123/ https://sentry.io/.../issues/456/"
    - "What's the error in issue 123?"
    - "Show me the details of these Sentry errors: [URLs or IDs]"

    This tool automatically extracts issue information and exports the complete error report(s)
    including stack traces, breadcrumbs, spans, request info, and context data to a readable text file.
    """
    try:
        # Parse Sentry URL pattern
        url_pattern = r'https?://([^/]+)/organizations/([^/]+)/issues/(\d+)'

        # Find all URLs in the input
        urls = re.findall(url_pattern, issue_url_or_id)

        # Extract issue IDs from URLs
        issue_ids = []
        base_url = None

        if urls:
            # We have URLs - extract IDs from them
            for domain, org, issue_id in urls:
                issue_ids.append(issue_id)

            # Try to get base_url from config
            config = load_config_safe()
            if config and not isinstance(config.get('error'), str):
                base_url = config.get('base_url')
            else:
                return f"❌ Cannot extract project info from URL. Please run 'initialize_config' first or provide the full issue ID with configured base_url."
        else:
            # No URLs found, treat as comma/space separated IDs
            # Split by common separators: comma, space, newline, #
            raw_ids = re.split(r'[,\s#]+', issue_url_or_id.strip())
            # Extract only digits from each part
            for raw_id in raw_ids:
                extracted = re.sub(r'[^\d]', '', raw_id)
                if extracted:
                    issue_ids.append(extracted)

        if not issue_ids:
            return "❌ No valid issue IDs or URLs found"

        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if len(issue_ids) == 1:
                output_file = f"sentry_issue_{issue_ids[0]}_{timestamp}.txt"
            else:
                output_file = f"sentry_issues_{timestamp}.txt"

        # Call internal export function
        return _do_export_issues(
            issue_ids=','.join(issue_ids),
            base_url=base_url,
            token=None,
            output_file=output_file,
            debug=debug
        )

    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def export_issues_tool(
    issue_ids: Annotated[str, Field(description="Comma-separated Issue IDs to export (e.g., '12345,67890,11111')")],
    base_url: Annotated[str | None, Field(description="Sentry API base URL (optional if already configured)")] = None,
    token: Annotated[str | None, Field(description="Sentry Auth Token (optional if already configured)")] = None,
    output_file: Annotated[str | None, Field(description="Output file name (optional, defaults to sentry_issues_TIMESTAMP.txt)")] = None,
    debug: Annotated[bool, Field(description="Enable debug mode to save raw JSON files")] = False
) -> str:
    """Export multiple Sentry issues to a plain text file (batch export).

    **Use this tool when the user wants to:**
    - Export multiple issues at once (e.g., "Export issues 123, 456, 789")
    - Batch download several error reports

    This tool exports complete error messages, stack traces, breadcrumbs, and context data
    for the specified Sentry issues. If base_url and token are not provided, it will use
    the saved configuration from ~/.config/export-sentry-issue/config.json.
    """
    return _do_export_issues(issue_ids, base_url, token, output_file, debug)


@mcp.tool()
def list_config() -> str:
    """Display the current saved Sentry configuration

    Shows the configured base URL and a masked version of the token.
    Returns an error if no configuration is found.
    """
    try:
        config = load_config_safe()

        if not config:
            return f"❌ No configuration found at {CONFIG_FILE}\nUse 'initialize_config' tool to set up your credentials."

        if "error" in config:
            return f"❌ {config['error']}\n{config['suggestion']}"

        token = config.get('token', '')
        masked_token = f"{token[:20]}..." if len(token) > 20 else "***"

        output = f"Configuration file: {CONFIG_FILE}\n"
        output += f"Base URL: {config.get('base_url', 'N/A')}\n"
        output += f"Token: {masked_token}"

        return output

    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def revoke_config() -> str:
    """Delete the saved Sentry configuration

    Removes the configuration file from ~/.config/export-sentry-issue/config.json.
    Note: You must manually revoke the token from Sentry:
      1. Go to: Settings → Account → API → Auth Tokens
      2. Find and delete the token
    """
    try:
        config = load_config_safe()

        if not config:
            return f"❌ No configuration found at {CONFIG_FILE}\nNothing to revoke."

        if "error" not in config:
            token = config.get('token', '')
            masked_token = f"{token[:20]}..." if len(token) > 20 else "***"

        if delete_config():
            output = f"✅ Configuration deleted from: {CONFIG_FILE}\n\n"
            output += "⚠️ IMPORTANT: Please manually revoke the token from Sentry:\n"
            output += "  1. Go to: Settings → Account → API → Auth Tokens\n"
            output += "  2. Find and delete the token"
            return output
        else:
            return "❌ Error: Could not delete configuration file"

    except Exception as e:
        return f"❌ Error: {str(e)}"


def main():
    """Main entry point for the MCP server"""
    parser = argparse.ArgumentParser(
        description="Export Sentry Issue MCP Server"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP/SSE transport instead of STDIO"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind HTTP server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port to bind HTTP server (default: 3001)"
    )

    args = parser.parse_args()

    if args.http:
        # Run with HTTP/SSE transport
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Route

        async def handle_sse(request):
            from mcp.server.sse import SseServerTransport
            from starlette.responses import StreamingResponse

            async with mcp.get_sse_transport() as (read, write):
                return StreamingResponse(
                    read(),
                    media_type="text/event-stream",
                )

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
            ]
        )

        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # Run with STDIO transport (default)
        mcp.run()


if __name__ == "__main__":
    main()
