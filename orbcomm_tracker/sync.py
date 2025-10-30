"""
Sync Orchestrator for ORBCOMM Tracker
Coordinates Gmail API, parsing, and database operations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from orbcomm_tracker.database import Database
from orbcomm_tracker.gmail_api import GmailAPI
from orbcomm_tracker.parser import ORBCOMMParser

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """Coordinates email fetching, parsing, and storage"""

    def __init__(self, inbox_number: int):
        """
        Initialize sync orchestrator

        Args:
            inbox_number: Inbox to sync (1 or 2)
        """
        self.inbox_number = inbox_number
        self.inbox_source = f"inbox{inbox_number}_continuous"

        # Initialize components
        self.db = Database()
        self.gmail = GmailAPI(inbox_number)
        self.parser = ORBCOMMParser(self.db)

    def sync(self, since_date: Optional[datetime] = None, force: bool = False) -> Dict:
        """
        Execute sync operation

        Args:
            since_date: Fetch emails after this date (None = auto-detect from last sync)
            force: If True, ignore historical_complete flag

        Returns:
            Dictionary with sync results
        """
        # Check if inbox is marked as historical_complete
        if not force:
            is_historical_complete = self.db.get_config(
                f"inbox{self.inbox_number}_historical_complete", default="false"
            )
            if is_historical_complete == "true":
                logger.info(
                    f"Inbox {self.inbox_number} marked as historical_complete, using continuous sync"
                )

        # Start sync logging
        sync_id = self.db.log_sync_start(self.inbox_source)

        try:
            # Determine date range
            if since_date is None:
                # Get last successful sync date
                last_sync = self.db.get_last_sync_date(self.inbox_source)
                if last_sync:
                    since_date = last_sync
                    logger.info(f"Last sync: {last_sync.isoformat()}")
                else:
                    # First sync - default to last 7 days
                    since_date = datetime.now() - timedelta(days=7)
                    logger.info("First sync - fetching last 7 days")

            # Fetch emails
            logger.info(f"Fetching emails since {since_date.isoformat()}")
            emails = self.gmail.fetch_new_emails(since_date=since_date)

            if not emails:
                logger.info("No new emails to process")
                self.db.log_sync_complete(
                    sync_id=sync_id,
                    emails_fetched=0,
                    emails_parsed=0,
                    errors_count=0,
                    status="success",
                )
                return {
                    "status": "success",
                    "emails_fetched": 0,
                    "emails_stored": 0,
                    "duplicates": 0,
                    "errors": 0,
                    "pairs_linked": 0,
                }

            # Parse and store
            logger.info(f"Processing {len(emails)} emails")
            counts = self.parser.parse_and_store_batch(emails, self.inbox_source)

            # Link notification pairs
            pairs_linked = 0
            if counts["stored"] > 0:
                logger.info("Linking notification pairs...")
                pairs_linked = self.parser.link_all_pairs(self.inbox_source)

            # Log completion
            self.db.log_sync_complete(
                sync_id=sync_id,
                emails_fetched=len(emails),
                emails_parsed=counts["stored"],
                errors_count=counts["errors"],
                status="success" if counts["errors"] == 0 else "partial",
            )

            result = {
                "status": "success" if counts["errors"] == 0 else "partial",
                "emails_fetched": len(emails),
                "emails_stored": counts["stored"],
                "duplicates": counts["duplicates"],
                "errors": counts["errors"],
                "pairs_linked": pairs_linked,
            }

            logger.info(f"Sync complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.db.log_sync_complete(
                sync_id=sync_id,
                emails_fetched=0,
                emails_parsed=0,
                errors_count=1,
                status="failed",
                error_log=str(e),
            )
            raise

    def get_sync_status(self) -> Dict:
        """
        Get current sync status and statistics

        Returns:
            Dictionary with sync status information
        """
        last_sync = self.db.get_last_sync_date(self.inbox_source)
        stats = self.db.get_current_stats()

        return {
            "inbox_number": self.inbox_number,
            "inbox_source": self.inbox_source,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "total_notifications": stats["total_notifications"],
            "open_count": stats["open_count"],
            "resolved_count": stats["resolved_count"],
            "avg_resolution_time_minutes": stats["avg_resolution_time_minutes"],
        }

    def archive_old_notifications(self, days: int = 180) -> int:
        """
        Archive notifications older than specified days

        Args:
            days: Archive notifications older than this many days

        Returns:
            Number of notifications archived
        """
        logger.info(f"Archiving notifications older than {days} days")
        archived = self.db.archive_old_notifications(days)
        logger.info(f"Archived {archived} notifications")
        return archived

    def save_stats_snapshot(self) -> bool:
        """
        Save current statistics as snapshot

        Returns:
            True if successful
        """
        logger.info("Saving stats snapshot")
        return self.db.save_stats_snapshot()

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
