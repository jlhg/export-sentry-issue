"""Configuration management for Sentry issue export tool."""

import json
import os
import re
import stat
from pathlib import Path

# Configuration paths
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
