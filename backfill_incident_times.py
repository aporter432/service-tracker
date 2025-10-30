#!/usr/bin/env python3
"""
Backfill Script: Extract Incident Times from Historical Resolved Emails

This script re-processes all resolved notifications to extract incident start/end times
from the HTML email body and updates the database with accurate incident durations.
"""

import logging

from orbcomm_processor import SimpleORBCOMMParser
from orbcomm_tracker.database import Database

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def backfill_incident_times():
    """
    Re-process all resolved notifications to extract incident times.
    """
    logger.info("=" * 80)
    logger.info("Starting Incident Times Backfill")
    logger.info("=" * 80)

    db = Database()
    parser = SimpleORBCOMMParser()
    cursor = db.conn.cursor()

    # Get all resolved notifications
    cursor.execute(
        """
        SELECT id, reference_number, raw_email_body, raw_email_subject, status
        FROM notifications
        WHERE status = 'Resolved' AND raw_email_body IS NOT NULL
    """
    )

    resolved_notifications = cursor.fetchall()
    total_count = len(resolved_notifications)
    logger.info(f"Found {total_count} resolved notifications to process")

    if total_count == 0:
        logger.info("No resolved notifications found. Exiting.")
        return

    updated_count = 0
    skipped_count = 0

    for row in resolved_notifications:
        notif_id = row["id"]
        reference_number = row["reference_number"]
        body = row["raw_email_body"]
        subject = row["raw_email_subject"]

        # Parse the email to extract incident times
        parsed = parser.parse_text(body, subject)

        incident_start = parsed.get("incident_start_time")
        incident_end = parsed.get("incident_end_time")
        incident_duration = parsed.get("incident_duration_minutes")

        if incident_start and incident_end and incident_duration is not None:
            # Update the notification with incident times
            cursor.execute(
                """
                UPDATE notifications
                SET incident_start_time = ?,
                    incident_end_time = ?,
                    incident_duration_minutes = ?
                WHERE id = ?
            """,
                (incident_start, incident_end, incident_duration, notif_id),
            )

            logger.info(
                f"✅ {reference_number}: {incident_duration} minutes ({incident_duration/60:.1f} hours)"
            )
            updated_count += 1
        else:
            logger.warning(
                f"⚠️  {reference_number}: No incident times found in email body"
            )
            skipped_count += 1

    db.conn.commit()

    logger.info("=" * 80)
    logger.info("Backfill Complete")
    logger.info(f"  Total processed: {total_count}")
    logger.info(f"  Updated: {updated_count}")
    logger.info(f"  Skipped (no times): {skipped_count}")
    logger.info("=" * 80)

    # Now re-link all pairs to update incident_duration_minutes in notification_pairs
    logger.info("\nRe-linking notification pairs...")
    cursor.execute("SELECT DISTINCT reference_number FROM notification_pairs")
    pairs = cursor.fetchall()

    linked_count = 0
    for pair in pairs:
        reference_number = pair["reference_number"]
        if db.link_notification_pair(reference_number):
            linked_count += 1
            logger.info(f"  Linked: {reference_number}")

    logger.info(f"\nRe-linked {linked_count} notification pairs")
    logger.info("=" * 80)

    # Show summary statistics
    logger.info("\nSummary Statistics:")
    cursor.execute(
        """
        SELECT
            COUNT(*) as total_pairs,
            AVG(time_to_resolve_minutes) as avg_email_time,
            AVG(incident_duration_minutes) as avg_incident_time
        FROM notification_pairs
        WHERE incident_duration_minutes IS NOT NULL
    """
    )
    stats = cursor.fetchone()

    if stats["total_pairs"] > 0:
        logger.info(
            f"  Paired notifications with incident times: {stats['total_pairs']}"
        )
        logger.info(
            f"  Average email processing time: {stats['avg_email_time']:.1f} minutes ({stats['avg_email_time']/60:.1f} hours)"
        )
        avg_time = stats["avg_incident_time"]
        logger.info(
            f"  Average incident duration: {avg_time:.1f} minutes "
            f"({avg_time/60:.1f} hours)"
        )

        time_difference = stats["avg_email_time"] - stats["avg_incident_time"]
        logger.info(
            f"  Time difference (email - incident): {time_difference:.1f} minutes ({time_difference/60:.1f} hours)"
        )

    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        backfill_incident_times()
    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        exit(1)
