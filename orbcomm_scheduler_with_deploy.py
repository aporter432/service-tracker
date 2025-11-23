#!/usr/bin/env python3
"""
ORBCOMM Daily Scheduler with Auto-Deploy
Automated daily sync, database export, git commit, and push to Render
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.sync import SyncOrchestrator  # noqa: E402

# Configure logging to file
log_dir = Path.home() / ".orbcomm" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"sync_deploy_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def export_database(db_path: str, backup_path: str) -> bool:
    """
    Export database to SQL file

    Args:
        db_path: Path to SQLite database
        backup_path: Path to save SQL backup

    Returns:
        True if successful
    """
    try:
        logger.info(f"Exporting database: {db_path} -> {backup_path}")

        # Use sqlite3 to dump database
        result = subprocess.run(
            ["sqlite3", db_path, ".dump"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Write to backup file
        with open(backup_path, "w") as f:
            f.write(result.stdout)

        # Get file size
        file_size = Path(backup_path).stat().st_size / 1024  # KB
        logger.info(f"Database exported successfully ({file_size:.1f} KB)")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to export database: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Export error: {e}")
        return False


def git_commit_and_push(project_dir: Path, message: str) -> bool:
    """
    Commit and push database changes to git

    Args:
        project_dir: Project directory
        message: Commit message

    Returns:
        True if successful
    """
    try:
        try:
            # Check if there are changes
            logger.info("Checking git status...")
            result = subprocess.run(
                ["git", "status", "--porcelain", "database_backup.sql"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            if not result.stdout.strip():
                logger.info("No database changes to commit")
                return True

            # Add database_backup.sql
            logger.info("Adding database_backup.sql to git...")
            subprocess.run(
                ["git", "add", "database_backup.sql"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Commit
            logger.info("Committing changes...")
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Push
            logger.info("Pushing to remote...")
            subprocess.run(
                ["git", "push"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info("✅ Database changes committed and pushed successfully")
            return True

        finally:
            # Return to original directory
            pass

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.error(f"Git error: {e}")
        return False


def run_daily_sync_with_deploy(inbox_numbers: list = None, auto_push: bool = True):
    """
    Run daily sync routine with automatic deployment

    Args:
        inbox_numbers: List of inboxes to sync (default: [1, 2] for both inboxes)
        auto_push: If True, automatically commit and push database changes

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    if inbox_numbers is None:
        inbox_numbers = [1, 2]  # Default: sync both inboxes

    logger.info("=" * 70)
    logger.info("ORBCOMM Daily Sync with Auto-Deploy Started")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Inboxes: {inbox_numbers}")
    logger.info(f"Auto-push: {auto_push}")
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

        # Get database path
        db_path = sync.db.db_path

        sync.close()

    except Exception as e:
        logger.error(f"Post-sync maintenance failed: {e}", exc_info=True)
        db_path = str(Path.home() / ".orbcomm" / "tracker.db")

    # Export database and push to git
    if auto_push:
        logger.info("=" * 70)
        logger.info("Exporting and Deploying Database")
        logger.info("=" * 70)

        project_dir = Path(__file__).parent.absolute()
        backup_path = project_dir / "database_backup.sql"

        # Export database
        if export_database(db_path, str(backup_path)):
            # Commit and push
            total_notifs = status["total_notifications"]
            open_count = status["open_count"]
            resolved_count = status["resolved_count"]

            commit_message = f"""Automated sync: Update database ({datetime.now().strftime('%Y-%m-%d')})

Total: {total_notifs} notifications ({open_count} open, {resolved_count} resolved)
Synced: {', '.join([f'Inbox {i}' for i in all_results.keys()])}

🤖 Automated sync via launchd scheduler"""

            if git_commit_and_push(project_dir, commit_message):
                logger.info("✅ Database exported and pushed to Render")
            else:
                logger.warning("⚠️  Database exported but git push failed")
        else:
            logger.error("❌ Database export failed - skipping git push")

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
    logger.info("Daily sync with deploy completed")
    logger.info("=" * 70)

    return 0


def main():
    """Main entry point"""
    # Default to both inboxes for continuous monitoring
    inbox_numbers = [1, 2]
    auto_push = True

    # Allow command-line override
    # Usage: python orbcomm_scheduler_with_deploy.py 1 2        (sync both, auto-push)
    # Usage: python orbcomm_scheduler_with_deploy.py --no-push  (sync only, no push)
    if "--no-push" in sys.argv:
        auto_push = False
        sys.argv.remove("--no-push")

    if len(sys.argv) > 1:
        try:
            inbox_numbers = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            logger.error(f"Invalid inbox number(s): {sys.argv[1:]}")
            return 1

    return run_daily_sync_with_deploy(inbox_numbers, auto_push)


if __name__ == "__main__":
    exit(main())
