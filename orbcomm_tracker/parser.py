"""
Enhanced ORBCOMM Parser with Database Integration
Parses emails and stores directly to database
"""

import sys
from pathlib import Path
from typing import Dict, Optional
import logging

# Add parent directory to path for importing orbcomm_processor
sys.path.insert(0, str(Path(__file__).parent.parent))

from orbcomm_processor import SimpleORBCOMMParser
from orbcomm_tracker.database import Database

logger = logging.getLogger(__name__)


class ORBCOMMParser:
    """Enhanced parser with database integration"""

    def __init__(self, db: Database):
        """
        Initialize parser with database connection

        Args:
            db: Database instance for storing parsed notifications
        """
        self.db = db
        self.parser = SimpleORBCOMMParser()

    def parse_and_store(self, email_data: Dict, inbox_source: str) -> Optional[int]:
        """
        Parse email and store notification in database

        Args:
            email_data: Email dictionary from GmailAPI
            inbox_source: Source identifier (e.g., 'inbox2_continuous')

        Returns:
            Notification ID if successful, None if duplicate or error
        """
        try:
            # Parse email using SimpleORBCOMMParser
            parsed = self.parser.parse_text(
                text=email_data['body'],
                subject=email_data['subject'],
                email_date=email_data.get('date_received')
            )

            # Check if already imported (by Gmail message ID)
            existing = self.db.get_notification_by_gmail_id(email_data['message_id'])
            if existing:
                logger.debug(f"Skipping duplicate: {parsed['reference_number']} (message_id: {email_data['message_id']})")
                return None

            # Add Gmail metadata
            parsed['gmail_message_id'] = email_data['message_id']
            parsed['thread_id'] = email_data['thread_id']
            parsed['inbox_source'] = inbox_source
            parsed['raw_email_body'] = email_data['body']
            parsed['raw_email_subject'] = email_data['subject']

            # Store in database
            notif_id = self.db.insert_notification(parsed)

            if notif_id:
                logger.info(f"Stored notification: {parsed['reference_number']} (ID: {notif_id})")
                return notif_id
            else:
                logger.warning(f"Failed to store notification: {parsed['reference_number']}")
                return None

        except Exception as e:
            logger.error(f"Error parsing and storing email: {e}")
            return None

    def parse_and_store_batch(self, emails: list, inbox_source: str) -> Dict[str, int]:
        """
        Parse and store multiple emails

        Args:
            emails: List of email dictionaries
            inbox_source: Source identifier

        Returns:
            Dictionary with counts: {'stored': N, 'duplicates': N, 'errors': N}
        """
        counts = {
            'stored': 0,
            'duplicates': 0,
            'errors': 0
        }

        for email_data in emails:
            try:
                notif_id = self.parse_and_store(email_data, inbox_source)
                if notif_id:
                    counts['stored'] += 1
                else:
                    counts['duplicates'] += 1
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                counts['errors'] += 1

        return counts

    def link_pairs_for_reference(self, reference_number: str) -> bool:
        """
        Link Open/Resolved pairs for a reference number

        Args:
            reference_number: Notification reference (e.g., 'S-003141')

        Returns:
            True if pair was linked successfully
        """
        try:
            return self.db.link_notification_pair(reference_number)
        except Exception as e:
            logger.error(f"Error linking pair {reference_number}: {e}")
            return False

    def link_all_pairs(self, inbox_source: Optional[str] = None) -> int:
        """
        Link all Open/Resolved pairs in database

        Args:
            inbox_source: Optional filter by inbox source

        Returns:
            Number of pairs linked
        """
        try:
            cursor = self.db.conn.cursor()

            if inbox_source:
                cursor.execute('''
                    SELECT DISTINCT reference_number
                    FROM notifications
                    WHERE inbox_source = ?
                ''', (inbox_source,))
            else:
                cursor.execute('SELECT DISTINCT reference_number FROM notifications')

            refs = [row[0] for row in cursor.fetchall()]

            linked = 0
            for ref in refs:
                if self.link_pairs_for_reference(ref):
                    linked += 1

            logger.info(f"Linked {linked} notification pairs")
            return linked

        except Exception as e:
            logger.error(f"Error linking all pairs: {e}")
            return 0
