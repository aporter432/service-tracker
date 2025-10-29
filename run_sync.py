#!/usr/bin/env python3
"""
Manual Sync Runner
Run this to manually sync ORBCOMM emails from inbox 2
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.sync import SyncOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Sync ORBCOMM notifications from Gmail'
    )
    parser.add_argument(
        '--inbox',
        type=int,
        default=2,
        help='Inbox number to sync (default: 2 for continuous monitoring)'
    )
    parser.add_argument(
        '--days',
        type=int,
        help='Number of days to look back (overrides last sync date)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force sync even if marked as historical_complete'
    )
    parser.add_argument(
        '--archive',
        type=int,
        help='Archive notifications older than N days'
    )
    parser.add_argument(
        '--snapshot',
        action='store_true',
        help='Save stats snapshot after sync'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show sync status and exit (no sync)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print(f"  ORBCOMM Sync - Inbox {args.inbox}")
    print("=" * 70)
    print()

    try:
        # Initialize sync orchestrator
        sync = SyncOrchestrator(args.inbox)

        # Status only mode
        if args.status:
            status = sync.get_sync_status()
            print("📊 Current Status")
            print("-" * 70)
            print(f"Inbox:                  {status['inbox_number']} ({status['inbox_source']})")
            print(f"Last sync:              {status['last_sync'] or 'Never'}")
            print(f"Total notifications:    {status['total_notifications']}")
            print(f"Open:                   {status['open_count']}")
            print(f"Resolved:               {status['resolved_count']}")
            print(f"Avg resolution time:    {status['avg_resolution_time_minutes']:.1f} minutes")
            print()
            return 0

        # Determine since_date
        since_date = None
        if args.days:
            since_date = datetime.now() - timedelta(days=args.days)
            print(f"📅 Looking back {args.days} days (since {since_date.strftime('%Y-%m-%d')})")
            print()

        # Run sync
        print("🔄 Starting sync...")
        print()
        result = sync.sync(since_date=since_date, force=args.force)

        # Display results
        print()
        print("=" * 70)
        print("  Sync Results")
        print("=" * 70)
        print(f"Status:           {result['status'].upper()}")
        print(f"Emails fetched:   {result['emails_fetched']}")
        print(f"Emails stored:    {result['emails_stored']}")
        print(f"Duplicates:       {result['duplicates']}")
        print(f"Errors:           {result['errors']}")
        print(f"Pairs linked:     {result['pairs_linked']}")
        print()

        # Archive old notifications if requested
        if args.archive:
            print(f"📦 Archiving notifications older than {args.archive} days...")
            archived = sync.archive_old_notifications(args.archive)
            print(f"✅ Archived {archived} notifications")
            print()

        # Save stats snapshot if requested
        if args.snapshot:
            print("📸 Saving stats snapshot...")
            sync.save_stats_snapshot()
            print("✅ Snapshot saved")
            print()

        # Show current stats
        status = sync.get_sync_status()
        print("=" * 70)
        print("  Current Database Stats")
        print("=" * 70)
        print(f"Total notifications:    {status['total_notifications']}")
        print(f"Open:                   {status['open_count']}")
        print(f"Resolved:               {status['resolved_count']}")
        print(f"Avg resolution time:    {status['avg_resolution_time_minutes']:.1f} minutes")
        print()

        print("=" * 70)
        print("✅ Sync complete!")
        print("=" * 70)
        print()

        sync.close()
        return 0 if result['status'] == 'success' else 1

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print()
        print("Please authenticate inbox first:")
        print(f"  ./venv/bin/python3 setup_gmail_auth.py --inbox {args.inbox} --email YOUR_EMAIL")
        return 1
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        print()
        print(f"❌ Sync failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
