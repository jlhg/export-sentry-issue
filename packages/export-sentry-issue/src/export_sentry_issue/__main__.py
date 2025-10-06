#!/usr/bin/env python3
"""Command-line interface for Sentry issue export tool."""

import argparse
import getpass
import os
import sys

import requests

from .config import (
    CONFIG_FILE,
    parse_base_url,
    save_config,
    load_config,
    delete_config,
)
from .core import export_issues, revoke_token


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
    print(f"  export-sentry-issue export --ids \"12345,67890\"")


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
        print("  1. Run 'export-sentry-issue init' to save your token")
        print("  2. Use --token parameter")
        print("  3. Set SENTRY_TOKEN environment variable")
        sys.exit(1)

    if not args.base_url:
        print("Error: No base URL provided.")
        print("Please either:")
        print("  1. Run 'export-sentry-issue init' to save your configuration")
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


def main():
    parser = argparse.ArgumentParser(
        description='Export Sentry issues to plain text file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Initialize (first time setup)
  export-sentry-issue init

  # Export issues (using saved configuration)
  export-sentry-issue export --ids "12345,67890"

  # Export issues (with explicit token)
  export-sentry-issue export --base-url "https://sentry.example.com/api/0/projects/my-org/my-project/issues/" --ids "12345,67890" --token "your_token"

  # Revoke token and delete configuration
  export-sentry-issue revoke
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
