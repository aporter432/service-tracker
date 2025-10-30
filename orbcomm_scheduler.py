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


def run_daily_sync(inbox_number: int = 2):
    """
    Run daily sync routine

    Args:
        inbox_number: Inbox to sync (default: 2 for continuous monitoring)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    logger.info("=" * 70)
    logger.info("ORBCOMM Daily Sync Started")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Inbox: {inbox_number}")
    logger.info("=" * 70)

    try:
        # Initialize sync orchestrator
        sync = SyncOrchestrator(inbox_number)

        # Run sync (auto-detects last sync date)
        logger.info("Running sync...")
        result = sync.sync()

        logger.info(f"Sync results: {result}")

        # Archive old notifications (180 days)
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
        logger.info("Final Status:")
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

        logger.info("Daily sync completed successfully")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"Daily sync failed: {e}", exc_info=True)
        logger.error("=" * 70)
        return 1


def main():
    """Main entry point"""
    # Default to inbox 2 for continuous monitoring
    inbox_number = 2

    # Allow command-line override
    if len(sys.argv) > 1:
        try:
            inbox_number = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid inbox number: {sys.argv[1]}")
            return 1

    return run_daily_sync(inbox_number)


if __name__ == "__main__":
    exit(main())
