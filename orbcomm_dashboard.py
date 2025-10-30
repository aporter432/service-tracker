#!/usr/bin/env python3
"""
ORBCOMM Tracker Web Dashboard
Flask-based web interface for viewing notifications and stats
"""

import csv
import io
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from orbcomm_tracker.database import Database  # noqa: E402
from orbcomm_tracker.sync import SyncOrchestrator  # noqa: E402

app = Flask(__name__)
app.config["SECRET_KEY"] = "orbcomm-tracker-2024"


# ==================== Helper Functions ====================


def get_db():
    """Get database instance"""
    return Database()


def format_duration(minutes):
    """Format duration in minutes to human-readable string"""
    if minutes is None or minutes == 0:
        return "N/A"

    hours = minutes / 60
    if hours < 1:
        return f"{int(minutes)}m"
    elif hours < 24:
        return f"{hours:.1f}h"
    else:
        days = hours / 24
        return f"{days:.1f}d"


def format_date(date_str):
    """Format ISO date string to readable format"""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %d, %Y %H:%M")
    except (ValueError, AttributeError):
        return date_str


app.jinja_env.filters["format_duration"] = format_duration
app.jinja_env.filters["format_date"] = format_date


# ==================== Routes ====================


@app.route("/")
def index():
    """Main dashboard page"""
    db = get_db()

    # Get current stats
    stats = db.get_current_stats()

    # Get recent notifications (last 20)
    notifications = db.get_all_notifications(include_archived=False)[:20]

    # Get truly open issues (Open/Continuing status with NO Resolved notification)
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT n.*
        FROM notifications n
        WHERE n.status IN ('Open', 'Continuing')
        AND n.is_archived = 0
        AND n.reference_number NOT IN (
            SELECT reference_number
            FROM notifications
            WHERE status = 'Resolved'
        )
        ORDER BY n.date_received DESC
    """
    )
    open_notifications = [dict(row) for row in cursor.fetchall()]

    # Get last sync info
    last_sync = db.get_last_sync_date("inbox2_continuous")

    # Get sync history
    sync_history = db.get_sync_history(limit=5)

    db.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        notifications=notifications,
        open_notifications=open_notifications,
        last_sync=last_sync,
        sync_history=sync_history,
    )


@app.route("/notifications")
def notifications():
    """Notifications list page with filtering"""
    db = get_db()

    # Get filter parameters
    status_filter = request.args.get("status", "all")
    platform_filter = request.args.get("platform", "all")
    include_archived = request.args.get("archived", "no") == "yes"

    # Get all notifications
    if status_filter != "all":
        notifs = db.get_notifications_by_status(status_filter, include_archived)
    else:
        notifs = db.get_all_notifications(include_archived)

    # Filter by platform
    if platform_filter != "all":
        notifs = [n for n in notifs if n["platform"] == platform_filter]

    # Get stats for sidebar
    stats = db.get_current_stats()

    db.close()

    return render_template(
        "notifications.html",
        notifications=notifs,
        stats=stats,
        status_filter=status_filter,
        platform_filter=platform_filter,
        include_archived=include_archived,
    )


@app.route("/notification/<int:notif_id>")
def notification_detail(notif_id):
    """Notification detail page"""
    db = get_db()

    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM notifications WHERE id = ?", (notif_id,))
    row = cursor.fetchone()

    if not row:
        db.close()
        return "Notification not found", 404

    notification = dict(row)

    # Check if this reference number has been resolved (even if this notification shows "Open")
    cursor.execute(
        """
        SELECT id, date_received, status
        FROM notifications
        WHERE reference_number = ?
        AND status = 'Resolved'
        ORDER BY date_received DESC
        LIMIT 1
    """,
        (notification["reference_number"],),
    )
    resolved_row = cursor.fetchone()
    has_been_resolved = resolved_row is not None
    resolved_notification = dict(resolved_row) if resolved_row else None

    # Get paired notification if exists
    paired = None
    cursor.execute(
        """
        SELECT * FROM notification_pairs WHERE reference_number = ?
    """,
        (notification["reference_number"],),
    )
    pair_row = cursor.fetchone()

    if pair_row:
        pair_dict = dict(pair_row)
        # Get the other notification in the pair
        other_id = (
            pair_dict["resolved_notification_id"]
            if notification["status"] == "Open"
            else pair_dict["open_notification_id"]
        )
        if other_id:
            cursor.execute("SELECT * FROM notifications WHERE id = ?", (other_id,))
            paired = dict(cursor.fetchone())

    db.close()

    return render_template(
        "notification_detail.html",
        notification=notification,
        paired=paired,
        has_been_resolved=has_been_resolved,
        resolved_notification=resolved_notification,
    )


@app.route("/stats")
def stats():
    """Statistics and charts page"""
    db = get_db()

    # Current stats
    current_stats = db.get_current_stats()

    # Historical stats (last 30 days)
    historical = db.get_historical_stats(days=30)

    # Platform breakdown
    platform_stats = current_stats["platform_breakdown"]

    # Event type breakdown
    event_stats = current_stats["event_type_breakdown"]

    db.close()

    return render_template(
        "stats.html",
        current_stats=current_stats,
        historical=historical,
        platform_stats=platform_stats,
        event_stats=event_stats,
    )


@app.route("/api/sync", methods=["POST"])
def api_sync():
    """Trigger manual sync"""
    try:
        sync = SyncOrchestrator(inbox_number=2)
        result = sync.sync()
        sync.close()

        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """Get current stats as JSON"""
    db = get_db()
    stats = db.get_current_stats()
    last_sync = db.get_last_sync_date("inbox2_continuous")
    db.close()

    return jsonify(
        {"stats": stats, "last_sync": last_sync.isoformat() if last_sync else None}
    )


@app.route("/export/csv")
def export_csv():
    """Export notifications to CSV"""
    db = get_db()

    # Get filter parameters
    status_filter = request.args.get("status", "all")
    include_archived = request.args.get("archived", "no") == "yes"

    # Get notifications
    if status_filter != "all":
        notifs = db.get_notifications_by_status(status_filter, include_archived)
    else:
        notifs = db.get_all_notifications(include_archived)

    db.close()

    # Create CSV in memory
    output = io.StringIO()
    fieldnames = [
        "reference_number",
        "date_received",
        "time_received",
        "platform",
        "event_type",
        "status",
        "scheduled_date",
        "scheduled_time",
        "duration",
        "affected_services",
        "summary",
        "time_to_resolve_minutes",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for notif in notifs:
        # Truncate summary for CSV
        if notif.get("summary") and len(notif["summary"]) > 200:
            notif["summary"] = notif["summary"][:197] + "..."
        writer.writerow(notif)

    # Prepare response
    output.seek(0)
    filename = f"orbcomm_notifications_{datetime.now().strftime('%Y%m%d')}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


# ==================== Error Handlers ====================


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", error="Internal server error"), 500


# ==================== Main ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ORBCOMM Tracker Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("=" * 70)
    print("  ORBCOMM Tracker Dashboard")
    print("=" * 70)
    print(f"  URL: http://{args.host}:{args.port}")
    print("=" * 70)
    print()

    app.run(host=args.host, port=args.port, debug=args.debug)
