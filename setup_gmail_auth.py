#!/usr/bin/env python3
"""
Gmail API Authentication Setup
Handles OAuth authentication for multiple Gmail inboxes
"""

import argparse
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope (read-only)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate_inbox(inbox_number: int, email: str):
    """
    Authenticate a Gmail inbox and save credentials.

    Args:
        inbox_number: Inbox identifier (1, 2, etc.)
        email: Gmail address being authenticated
    """
    # Set up paths
    config_dir = Path.home() / ".orbcomm" / f"inbox{inbox_number}"
    config_dir.mkdir(parents=True, exist_ok=True)

    credentials_file = config_dir / "credentials.json"
    token_file = config_dir / "token.json"

    # Check if credentials.json exists
    if not credentials_file.exists():
        print(f"❌ Error: credentials.json not found at {credentials_file}")
        print(
            "\nPlease download OAuth credentials from Google Cloud Console and save to:"
        )
        print(f"   {credentials_file}")
        return False

    print(f"\n🔐 Authenticating Inbox {inbox_number}: {email}")
    print(f"   Credentials: {credentials_file}")
    print(f"   Token will be saved to: {token_file}")

    creds = None

    # Load existing token if available
    if token_file.exists():
        print("\n📋 Found existing token, attempting to load...")
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("\n🌐 Opening browser for authentication...")
            print(f"   Please sign in to: {email}")
            print("   Grant permissions when prompted")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(token_file, "w") as token:
            token.write(creds.to_json())
        print(f"\n✅ Token saved to: {token_file}")

    # Test the connection
    try:
        print("\n🧪 Testing connection...")
        service = build("gmail", "v1", credentials=creds)

        # Get user profile to verify
        profile = service.users().getProfile(userId="me").execute()
        authenticated_email = profile["emailAddress"]

        print("✅ Successfully authenticated!")
        print(f"   Email: {authenticated_email}")

        # Quick count of ORBCOMM emails
        query = 'subject:"ORBCOMM Service Notification:"'
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=1)
            .execute()
        )

        total = results.get("resultSizeEstimate", 0)
        print(f"   Found ~{total} ORBCOMM notifications")

        return True

    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Authenticate Gmail inbox for ORBCOMM tracker"
    )
    parser.add_argument(
        "--inbox", type=int, required=True, help="Inbox number (1, 2, etc.)"
    )
    parser.add_argument(
        "--email", type=str, required=True, help="Gmail address to authenticate"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  ORBCOMM Tracker - Gmail Authentication Setup")
    print("=" * 60)

    success = authenticate_inbox(args.inbox, args.email)

    if success:
        print("\n" + "=" * 60)
        print("  ✅ Authentication Complete!")
        print("=" * 60)
        print(f"\nInbox {args.inbox} is ready to use.")
        print("\nNext steps:")
        print("  1. If you have another inbox, run this script again with --inbox 2")
        print("  2. Test all connections: python3 test_gmail_connection.py")
        print("  3. Run initial sync: python3 orbcomm_sync.py --initial-sync")
    else:
        print("\n" + "=" * 60)
        print("  ❌ Authentication Failed")
        print("=" * 60)
        print("\nPlease check the error messages above and try again.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
