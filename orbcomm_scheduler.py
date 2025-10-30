#!/usr/bin/env python3
"""
ORBCOMM Daily Scheduler
Automated daily sync, archiving, and stats tracking
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.sync import SyncOrchestrator  # noqa: E402

# Configure logging to file
log_dir = Path.home() / ".orbcomm" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"sync_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_daily_sync(inbox_numbers: list = None):
    """
    Run daily sync routine for multiple inboxes

    Args:
        inbox_numbers: List of inboxes to sync (default: [1, 2] for both inboxes)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    if inbox_numbers is None:
        inbox_numbers = [1, 2]  # Default: sync both inboxes

    logger.info("=" * 70)
    logger.info("ORBCOMM Daily Sync Started")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Inboxes: {inbox_numbers}")
    logger.info("=" * 70)

    all_results = {}
    failed_inboxes = []

    # Sync each inbox
    for inbox_number in inbox_numbers:
        try:
            logger.info("=" * 70)
            logger.info(f"Syncing Inbox {inbox_number}")
            logger.info("=" * 70)

            # Initialize sync orchestrator
            sync = SyncOrchestrator(inbox_number)

            # Run sync (auto-detects last sync date)
            logger.info(f"Running sync for inbox {inbox_number}...")
            result = sync.sync()

            logger.info(f"Inbox {inbox_number} sync results: {result}")
            all_results[inbox_number] = result

            sync.close()

        except FileNotFoundError as e:
            logger.warning(f"Inbox {inbox_number} not authenticated: {e}")
            logger.warning(f"Skipping inbox {inbox_number}")
            failed_inboxes.append(inbox_number)
            continue
        except Exception as e:
            logger.error(f"Inbox {inbox_number} sync failed: {e}", exc_info=True)
            failed_inboxes.append(inbox_number)
            continue

    # If all inboxes failed, exit with error
    if len(failed_inboxes) == len(inbox_numbers):
        logger.error("All inboxes failed to sync")
        logger.error("=" * 70)
        return 1

    # Post-sync maintenance (using first successful inbox)
    try:
        successful_inbox = [i for i in inbox_numbers if i not in failed_inboxes][0]
        sync = SyncOrchestrator(successful_inbox)

        # Archive old notifications (180 days)
        logger.info("=" * 70)
        logger.info("Running post-sync maintenance...")
        logger.info("Archiving old notifications...")
        archived = sync.archive_old_notifications(days=180)
        logger.info(f"Archived {archived} notifications")

        # Save stats snapshot
        logger.info("Saving stats snapshot...")
        sync.save_stats_snapshot()
        logger.info("Stats snapshot saved")

        # Get final status
        status = sync.get_sync_status()
        logger.info("=" * 70)
        logger.info("Final Database Status:")
        logger.info(f"  Total notifications: {status['total_notifications']}")
        logger.info(f"  Open: {status['open_count']}")
        logger.info(f"  Resolved: {status['resolved_count']}")
        logger.info(
            f"  Avg resolution: {status['avg_resolution_time_minutes']:.1f} minutes"
        )
        logger.info("=" * 70)

        # Database maintenance (vacuum)
        logger.info("Running database maintenance...")
        sync.db.vacuum()
        logger.info("Database vacuumed")

        sync.close()

    except Exception as e:
        logger.error(f"Post-sync maintenance failed: {e}", exc_info=True)

    # Summary
    logger.info("=" * 70)
    logger.info("Sync Summary:")
    for inbox_number, result in all_results.items():
        logger.info(
            f"  Inbox {inbox_number}: {result['emails_fetched']} fetched, "
            f"{result['emails_stored']} stored"
        )
    if failed_inboxes:
        logger.warning(f"  Failed inboxes: {failed_inboxes}")
    logger.info("Daily sync completed")
    logger.info("=" * 70)

    return 0


def main():
    """Main entry point"""
    # Default to both inboxes for continuous monitoring
    inbox_numbers = [1, 2]

    # Allow command-line override
    # Usage: python orbcomm_scheduler.py 1 2  (sync inboxes 1 and 2)
    # Usage: python orbcomm_scheduler.py 1    (sync only inbox 1)
    if len(sys.argv) > 1:
        try:
            inbox_numbers = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            logger.error(f"Invalid inbox number(s): {sys.argv[1:]}")
            return 1

    return run_daily_sync(inbox_numbers)


if __name__ == "__main__":
    exit(main())
