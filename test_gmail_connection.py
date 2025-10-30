#!/usr/bin/env python3
"""
Test Gmail API connections for all configured inboxes
"""

from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def test_inbox(inbox_number: int):
    """Test connection for a specific inbox."""
    config_dir = Path.home() / ".orbcomm" / f"inbox{inbox_number}"
    token_file = config_dir / "token.json"

    if not token_file.exists():
        return None, f"Token not found at {token_file}"

    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

        if not creds.valid:
            return None, "Token is invalid or expired"

        # Build service
        service = build("gmail", "v1", credentials=creds)

        # Get profile
        profile = service.users().getProfile(userId="me").execute()
        email = profile["emailAddress"]

        # Count ORBCOMM emails
        query = 'subject:"ORBCOMM Service Notification:"'
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=1)
            .execute()
        )

        total_count = results.get("resultSizeEstimate", 0)

        # Get latest email date if any exist
        latest_date = None
        if results.get("messages"):
            msg_id = results["messages"][0]["id"]
            msg = (
                service.users()
                .messages()
                .get(
                    userId="me", id=msg_id, format="metadata", metadataHeaders=["Date"]
                )
                .execute()
            )

            for header in msg["payload"]["headers"]:
                if header["name"] == "Date":
                    latest_date = header["value"]
                    break

        return {
            "email": email,
            "count": total_count,
            "latest_date": latest_date,
            "status": "connected",
        }, None

    except Exception as e:
        return None, str(e)


def main():
    print("=" * 70)
    print("  ORBCOMM Tracker - Gmail Connection Test")
    print("=" * 70)
    print()

    inboxes_found = 0
    inboxes_connected = 0

    # Test up to 5 possible inboxes
    for inbox_num in range(1, 6):
        config_dir = Path.home() / ".orbcomm" / f"inbox{inbox_num}"

        if not config_dir.exists():
            if inbox_num <= 2:  # Only mention missing for first 2
                print(f"⚪ Inbox {inbox_num}: Not configured")
            break

        inboxes_found += 1

        result, error = test_inbox(inbox_num)

        if error:
            print(f"❌ Inbox {inbox_num}: Failed")
            print(f"   Error: {error}")
        else:
            inboxes_connected += 1
            print(f"✅ Inbox {inbox_num} ({result['email']}): Connected")
            print(f"   Found {result['count']} ORBCOMM notifications")
            if result["latest_date"]:
                print(f"   Latest: {result['latest_date'][:25]}...")
        print()

    print("=" * 70)

    if inboxes_connected == 0:
        print("❌ No inboxes are authenticated")
        print("\nTo authenticate:")
        print("  python3 setup_gmail_auth.py --inbox 1 --email your-email@gmail.com")
        return 1

    elif inboxes_found == inboxes_connected:
        print(f"🎉 All {inboxes_connected} inbox(es) authenticated successfully!")
        print("\nReady to sync!")
        print("  python3 orbcomm_sync.py --initial-sync")
        return 0

    else:
        print(f"⚠️  {inboxes_connected}/{inboxes_found} inboxes connected")
        print("\nSome inboxes need re-authentication.")
        return 1


if __name__ == "__main__":
    exit(main())
