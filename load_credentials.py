#!/usr/bin/env python3
"""Load Gmail credentials from environment variables for Render deployment."""
import base64
import json
import os
from pathlib import Path


def load_credentials_from_env():
    """Load credentials from base64-encoded environment variables."""
    # Define credential paths
    credentials = {
        "inbox1_creds": "/app/data/inbox1/credentials.json",
        "inbox1_token": "/app/data/inbox1/token.json",
        "inbox2_creds": "/app/data/inbox2/credentials.json",
        "inbox2_token": "/app/data/inbox2/token.json",
    }

    # Create directories
    Path("/app/data/inbox1").mkdir(parents=True, exist_ok=True)
    Path("/app/data/inbox2").mkdir(parents=True, exist_ok=True)

    # Load from environment variables if present
    env_vars = {
        "INBOX1_CREDENTIALS": credentials["inbox1_creds"],
        "INBOX1_TOKEN": credentials["inbox1_token"],
        "INBOX2_CREDENTIALS": credentials["inbox2_creds"],
        "INBOX2_TOKEN": credentials["inbox2_token"],
    }

    for env_var, file_path in env_vars.items():
        if env_var in os.environ:
            try:
                # Decode base64
                decoded = base64.b64decode(os.environ[env_var])
                # Parse JSON to validate
                json_data = json.loads(decoded)
                # Write to file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f)
                print(f"✓ Loaded {env_var} to {file_path}")
            except (ValueError, KeyError, OSError) as e:
                print(f"✗ Failed to load {env_var}: {e}")
        else:
            print(f"○ {env_var} not found in environment")


if __name__ == "__main__":
    load_credentials_from_env()
