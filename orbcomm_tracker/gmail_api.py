"""
Gmail API Integration Layer
Handles authentication and email fetching for ORBCOMM tracker
"""

import base64
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SEARCH_QUERY = 'subject:"ORBCOMM Service Notification:"'


class GmailAPI:
    """Gmail API wrapper for ORBCOMM notifications"""

    def __init__(self, inbox_number: int):
        """
        Initialize Gmail API client

        Args:
            inbox_number: Inbox identifier (1 or 2)
        """
        self.inbox_number = inbox_number
        # Use ORBCOMM_DATA_DIR env var for production (Render), fallback to home dir for local dev
        data_dir = os.environ.get("ORBCOMM_DATA_DIR", str(Path.home() / ".orbcomm"))
        self.config_dir = Path(data_dir) / f"inbox{inbox_number}"
        self.token_file = self.config_dir / "token.json"
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API, refreshing token if expired"""
        if not self.token_file.exists():
            raise FileNotFoundError(
                f"Inbox {self.inbox_number} not authenticated. "
                f"Run: ./venv/bin/python3 setup_gmail_auth.py --inbox {self.inbox_number}"
            )

        creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            logger.info(f"Refreshing expired token for inbox {self.inbox_number}")
            creds.refresh(Request())
            # Save refreshed token
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())
            logger.info(f"Token refreshed and saved for inbox {self.inbox_number}")

        self.service = build("gmail", "v1", credentials=creds)
        logger.info(f"Authenticated inbox {self.inbox_number}")

    def fetch_new_emails(
        self, since_date: Optional[datetime] = None, max_results: int = 100
    ) -> List[Dict]:
        """
        Fetch new ORBCOMM notification emails

        Args:
            since_date: Only fetch emails after this date (None = last 7 days)
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with full content
        """
        if since_date is None:
            # Default: last 7 days
            since_date = datetime.now() - timedelta(days=7)

        # Format date for Gmail query (YYYY/MM/DD)
        date_str = since_date.strftime("%Y/%m/%d")
        query = f"{SEARCH_QUERY} after:{date_str}"

        logger.info(f"Fetching emails with query: {query}")

        try:
            # Get message IDs
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                logger.info("No new emails found")
                return []

            logger.info(f"Found {len(messages)} new emails")

            # Fetch full content for each message
            emails = []
            for msg in messages:
                msg_id = msg["id"]
                full_msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="full")
                    .execute()
                )

                email_data = self._extract_email_content(full_msg)
                emails.append(email_data)

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    def _extract_email_content(self, message_data: Dict) -> Dict:
        """
        Extract subject, body, and metadata from Gmail message

        Args:
            message_data: Raw Gmail API message response

        Returns:
            Dictionary with extracted email content
        """
        headers = message_data["payload"]["headers"]

        # Extract headers
        subject = ""
        date_received = ""
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            elif header["name"] == "Date":
                date_received = header["value"]

        # Extract body
        body = ""
        if "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                        break
        else:
            if "data" in message_data["payload"]["body"]:
                body = base64.urlsafe_b64decode(
                    message_data["payload"]["body"]["data"]
                ).decode("utf-8")

        return {
            "message_id": message_data["id"],
            "thread_id": message_data["threadId"],
            "subject": subject,
            "body": body,
            "date_received": date_received,
            "inbox_number": self.inbox_number,
        }

    def get_email_count(self, since_date: Optional[datetime] = None) -> int:
        """
        Get count of ORBCOMM emails without fetching full content

        Args:
            since_date: Count emails after this date

        Returns:
            Number of matching emails
        """
        if since_date is None:
            since_date = datetime.now() - timedelta(days=7)

        date_str = since_date.strftime("%Y/%m/%d")
        query = f"{SEARCH_QUERY} after:{date_str}"

        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=1)
                .execute()
            )

            # Gmail returns resultSizeEstimate for total count
            return results.get("resultSizeEstimate", 0)

        except Exception as e:
            logger.error(f"Error getting email count: {e}")
            return 0
