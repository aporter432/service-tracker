#!/usr/bin/env python3
"""
Manual Sync Runner
Run this to manually sync ORBCOMM emails from inbox 2
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.sync import SyncOrchestrator  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Sync ORBCOMM notifications from Gmail"
    )
    parser.add_argument(
        "--inbox",
        type=int,
        default=None,
        help="Inbox number to sync (if not specified with --all, defaults to 2)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all authenticated inboxes (1 and 2)",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to look back (overrides last sync date)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync even if marked as historical_complete",
    )
    parser.add_argument(
        "--archive", type=int, help="Archive notifications older than N days"
    )
    parser.add_argument(
        "--snapshot", action="store_true", help="Save stats snapshot after sync"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show sync status and exit (no sync)"
    )

    args = parser.parse_args()

    # Determine which inboxes to sync
    if args.all:
        inbox_numbers = [1, 2]
    elif args.inbox is not None:
        inbox_numbers = [args.inbox]
    else:
        inbox_numbers = [2]  # Default to inbox 2 for backward compatibility

    print("=" * 70)
    if len(inbox_numbers) > 1:
        print(f"  ORBCOMM Sync - Inboxes {', '.join(map(str, inbox_numbers))}")
    else:
        print(f"  ORBCOMM Sync - Inbox {inbox_numbers[0]}")
    print("=" * 70)
    print()

    try:
        all_results = {}
        failed_inboxes = []

        # Status only mode
        if args.status:
            for inbox_num in inbox_numbers:
                try:
                    sync = SyncOrchestrator(inbox_num)
                    status = sync.get_sync_status()
                    print(f"📊 Inbox {inbox_num} Status")
                    print("-" * 70)
                    print(f"Source:                 {status['inbox_source']}")
                    print(f"Last sync:              {status['last_sync'] or 'Never'}")
                    print(f"Total notifications:    {status['total_notifications']}")
                    print(f"Open:                   {status['open_count']}")
                    print(f"Resolved:               {status['resolved_count']}")
                    print(
                        f"Avg resolution time:    {status['avg_resolution_time_minutes']:.1f} minutes"
                    )
                    print()
                    sync.close()
                except FileNotFoundError:
                    print(f"⚠️  Inbox {inbox_num} not authenticated")
                    print()
            return 0

        # Determine since_date
        since_date = None
        if args.days:
            since_date = datetime.now() - timedelta(days=args.days)
            print(
                f"📅 Looking back {args.days} days (since {since_date.strftime('%Y-%m-%d')})"
            )
            print()

        # Run sync for each inbox
        for inbox_num in inbox_numbers:
            try:
                print("=" * 70)
                print(f"🔄 Starting sync for Inbox {inbox_num}...")
                print("=" * 70)
                print()

                sync = SyncOrchestrator(inbox_num)
                result = sync.sync(since_date=since_date, force=args.force)
                all_results[inbox_num] = result

                # Display results
                print()
                print("-" * 70)
                print(f"  Inbox {inbox_num} Sync Results")
                print("-" * 70)
                print(f"Status:           {result['status'].upper()}")
                print(f"Emails fetched:   {result['emails_fetched']}")
                print(f"Emails stored:    {result['emails_stored']}")
                print(f"Duplicates:       {result['duplicates']}")
                print(f"Errors:           {result['errors']}")
                print(f"Pairs linked:     {result['pairs_linked']}")
                print()

                sync.close()

            except FileNotFoundError as e:
                print(f"❌ Error: {e}")
                print(f"⚠️  Skipping inbox {inbox_num} - not authenticated")
                print()
                failed_inboxes.append(inbox_num)
                continue
            except Exception as e:
                logger.error(f"Inbox {inbox_num} sync failed: {e}", exc_info=True)
                print(f"❌ Inbox {inbox_num} sync failed: {e}")
                print()
                failed_inboxes.append(inbox_num)
                continue

        # If all inboxes failed, exit with error
        if len(failed_inboxes) == len(inbox_numbers):
            print("❌ All inboxes failed to sync")
            return 1

        # Post-sync operations (using first successful inbox)
        successful_inboxes = [i for i in inbox_numbers if i not in failed_inboxes]
        if successful_inboxes:
            sync = SyncOrchestrator(successful_inboxes[0])

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
            print(
                f"Avg resolution time:    {status['avg_resolution_time_minutes']:.1f} minutes"
            )
            print()

            sync.close()

        # Summary
        print("=" * 70)
        print("  Sync Summary")
        print("=" * 70)
        for inbox_num, result in all_results.items():
            print(
                f"Inbox {inbox_num}: {result['emails_fetched']} fetched, "
                f"{result['emails_stored']} stored"
            )
        if failed_inboxes:
            print(f"Failed: {', '.join(map(str, failed_inboxes))}")
        print()

        print("=" * 70)
        print("✅ Sync complete!")
        print("=" * 70)
        print()

        # Return error if any inbox failed
        return 0 if not failed_inboxes else 1

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        print()
        print(f"❌ Sync failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
