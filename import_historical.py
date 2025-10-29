#!/usr/bin/env python3
"""
Historical Email Import
One-time import of all ORBCOMM emails from an inbox
"""

import sys
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import base64
from email import message_from_bytes

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.database import Database
from orbcomm_processor import SimpleORBCOMMParser

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service(inbox_number: int):
    """Get authenticated Gmail service"""
    config_dir = Path.home() / '.orbcomm' / f'inbox{inbox_number}'
    token_file = config_dir / 'token.json'

    if not token_file.exists():
        print(f"❌ Error: Inbox {inbox_number} not authenticated")
        print(f"   Run: ./venv/bin/python3 setup_gmail_auth.py --inbox {inbox_number} --email YOUR_EMAIL")
        return None

    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    return build('gmail', 'v1', credentials=creds)


def extract_email_content(message_data):
    """Extract subject and body from Gmail message"""
    headers = message_data['payload']['headers']

    subject = ''
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
            break

    # Get email body
    body = ''
    if 'parts' in message_data['payload']:
        for part in message_data['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
    else:
        if 'data' in message_data['payload']['body']:
            body = base64.urlsafe_b64decode(message_data['payload']['body']['data']).decode('utf-8')

    # Get date
    date_received = None
    for header in headers:
        if header['name'] == 'Date':
            date_received = header['value']
            break

    return {
        'subject': subject,
        'body': body,
        'date_received': date_received,
        'message_id': message_data['id'],
        'thread_id': message_data['threadId']
    }


def import_historical_emails(inbox_number: int, inbox_email: str, max_emails: int = None):
    """Import all historical emails from an inbox"""
    print("=" * 70)
    print(f"  Historical Import - Inbox {inbox_number}")
    print("=" * 70)
    print(f"Email: {inbox_email}")
    print()

    # Get Gmail service
    service = get_gmail_service(inbox_number)
    if not service:
        return False

    # Initialize database
    db = Database()
    inbox_source = f"inbox{inbox_number}_historical"

    # Initialize parser
    parser = SimpleORBCOMMParser()

    print("🔍 Searching for ORBCOMM emails...")
    query = 'subject:"ORBCOMM Service Notification:"'

    try:
        # Get all message IDs (no date filter for historical)
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=500 if not max_emails else max_emails
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print("❌ No ORBCOMM emails found")
            return False

        total_emails = len(messages)
        print(f"✅ Found {total_emails} emails to import")
        print()

        # Process each email
        imported = 0
        duplicates = 0
        errors = 0

        print("📥 Importing emails...")
        print("-" * 70)

        for i, message in enumerate(messages, 1):
            msg_id = message['id']

            try:
                # Check if already imported
                existing = db.get_notification_by_gmail_id(msg_id)
                if existing:
                    duplicates += 1
                    print(f"[{i}/{total_emails}] ⏭️  Already imported: {existing['reference_number']}")
                    continue

                # Fetch full message
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                # Extract content
                email_content = extract_email_content(msg_data)

                # Parse with existing parser (pass email date from headers)
                parsed = parser.parse_text(
                    email_content['body'],
                    email_content['subject'],
                    email_date=email_content.get('date_received')
                )

                # Add Gmail metadata
                parsed['gmail_message_id'] = msg_id
                parsed['thread_id'] = email_content['thread_id']
                parsed['inbox_source'] = inbox_source
                parsed['raw_email_body'] = email_content['body']
                parsed['raw_email_subject'] = email_content['subject']

                # Store in database
                notif_id = db.insert_notification(parsed)

                if notif_id:
                    imported += 1
                    status_icon = "✅"
                    status = f"Imported: {parsed['reference_number']}"
                else:
                    duplicates += 1
                    status_icon = "⏭️"
                    status = "Duplicate"

                print(f"[{i}/{total_emails}] {status_icon} {status}")

                # Try to link pairs every 10 emails
                if imported % 10 == 0:
                    if parsed.get('reference_number'):
                        db.link_notification_pair(parsed['reference_number'])

            except Exception as e:
                errors += 1
                print(f"[{i}/{total_emails}] ❌ Error: {e}")

        print("-" * 70)
        print()
        print("📊 Import Summary")
        print("=" * 70)
        print(f"Total found:      {total_emails}")
        print(f"✅ Imported:      {imported}")
        print(f"⏭️  Duplicates:    {duplicates}")
        print(f"❌ Errors:        {errors}")
        print()

        # Link all remaining pairs
        if imported > 0:
            print("🔗 Linking Open/Resolved pairs...")
            # Get all unique reference numbers
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT reference_number
                FROM notifications
                WHERE inbox_source = ?
            ''', (inbox_source,))
            refs = [row[0] for row in cursor.fetchall()]

            linked = 0
            for ref in refs:
                if db.link_notification_pair(ref):
                    linked += 1

            print(f"✅ Linked {linked} notification pairs")
            print()

        # Mark historical import complete
        db.set_config(f'inbox{inbox_number}_historical_complete', 'true')
        db.set_config(f'inbox{inbox_number}_import_date', datetime.now().isoformat())
        db.set_config(f'inbox{inbox_number}_email', inbox_email)

        # Show stats
        print("📈 Database Stats")
        print("=" * 70)
        stats = db.get_current_stats()
        print(f"Total notifications: {stats['total_notifications']}")
        print(f"Open:                {stats['open_count']}")
        print(f"Resolved:            {stats['resolved_count']}")
        print(f"Avg resolution:      {stats['avg_resolution_time_minutes']:.1f} minutes")
        print()

        print("=" * 70)
        print("✅ Historical import complete!")
        print("=" * 70)
        print()
        print(f"Inbox {inbox_number} has been marked as historical import complete.")
        print("It will not be included in future daily syncs.")
        print()
        print("Next steps:")
        print(f"  1. Set up inbox 2 (continuous monitoring)")
        print(f"  2. Run: ./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email work@company.com")
        print(f"  3. Start dashboard: ./venv/bin/python3 orbcomm_dashboard.py")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Import all historical ORBCOMM emails from an inbox'
    )
    parser.add_argument(
        '--inbox',
        type=int,
        required=True,
        help='Inbox number (typically 1 for historical)'
    )
    parser.add_argument(
        '--email',
        type=str,
        help='Email address (optional, for display)'
    )
    parser.add_argument(
        '--max',
        type=int,
        help='Maximum emails to import (for testing)'
    )

    args = parser.parse_args()

    if not args.email:
        # Try to get from auth
        config_dir = Path.home() / '.orbcomm' / f'inbox{args.inbox}'
        token_file = config_dir / 'token.json'
        if token_file.exists():
            args.email = f"inbox{args.inbox}"

    success = import_historical_emails(args.inbox, args.email or "unknown", args.max)

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
