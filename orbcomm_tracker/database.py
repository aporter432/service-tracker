"""
Database layer for ORBCOMM Service Tracker
SQLite-based persistence with full CRUD operations
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for ORBCOMM notifications"""

    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = Path.home() / ".orbcomm" / "tracker.db"
        else:
            db_path = Path(db_path)

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self.conn = None
        self._connect()
        self._initialize_schema()

    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys

    def _initialize_schema(self):
        """Create database schema if not exists"""
        cursor = self.conn.cursor()

        # Notifications table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT NOT NULL,
                gmail_message_id TEXT UNIQUE NOT NULL,
                thread_id TEXT,
                inbox_source TEXT,

                -- Timestamps
                date_received DATETIME NOT NULL,
                time_received TIME,
                date_parsed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Classification
                platform TEXT CHECK(platform IN ('IDP', 'OGx', 'OGWS', 'Unknown')),
                event_type TEXT NOT NULL,
                status TEXT CHECK(status IN ('Open', 'Resolved', 'Continuing')) DEFAULT 'Open',
                priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')) DEFAULT 'Medium',

                -- Scheduling
                scheduled_date TEXT,
                scheduled_time TEXT,
                duration TEXT,

                -- Details
                affected_services TEXT,
                summary TEXT NOT NULL,
                raw_email_body TEXT,
                raw_email_subject TEXT,

                -- Resolution tracking
                resolution_date DATETIME,
                resolution_time TIME,
                time_to_resolve_minutes INTEGER,

                -- Incident tracking (from resolved email content)
                incident_start_time DATETIME,
                incident_end_time DATETIME,
                incident_duration_minutes INTEGER,

                -- Metadata
                is_archived BOOLEAN DEFAULT 0,
                notes TEXT
            )
        """
        )

        # Notification pairs for resolution tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT UNIQUE NOT NULL,
                open_notification_id INTEGER,
                resolved_notification_id INTEGER,
                time_to_resolve_minutes INTEGER,
                FOREIGN KEY (open_notification_id) REFERENCES notifications(id),
                FOREIGN KEY (resolved_notification_id) REFERENCES notifications(id)
            )
        """
        )

        # Stats snapshots for historical trends
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stats_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_notifications INTEGER,
                open_count INTEGER,
                resolved_count INTEGER,
                continuing_count INTEGER,
                avg_resolution_time_minutes REAL,
                platform_breakdown TEXT,
                event_type_breakdown TEXT
            )
        """
        )

        # Sync history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                sync_end DATETIME,
                inbox_source TEXT,
                emails_fetched INTEGER,
                emails_parsed INTEGER,
                errors_count INTEGER,
                last_email_date DATETIME,
                status TEXT CHECK(status IN ('success', 'partial', 'failed')),
                error_log TEXT
            )
        """
        )

        # Configuration
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_reference ON notifications(reference_number)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_date ON notifications(date_received)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_platform ON notifications(platform)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_gmail_id ON notifications(gmail_message_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_notifications_archived ON notifications(is_archived)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sync_history_date ON sync_history(sync_start)"
        )

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

        # Run migrations
        self._run_migrations()

    def _run_migrations(self):
        """Apply database migrations for existing databases"""
        cursor = self.conn.cursor()

        # Check if incident tracking columns exist in notifications table
        cursor.execute("PRAGMA table_info(notifications)")
        columns = [row[1] for row in cursor.fetchall()]

        if "incident_start_time" not in columns:
            logger.info(
                "Migrating database: Adding incident tracking columns to notifications"
            )
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN incident_start_time DATETIME"
            )
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN incident_end_time DATETIME"
            )
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN incident_duration_minutes INTEGER"
            )
            self.conn.commit()
            logger.info(
                "Migration complete: Incident tracking columns added to notifications"
            )

        # Check if incident_duration_minutes exists in notification_pairs table
        cursor.execute("PRAGMA table_info(notification_pairs)")
        pair_columns = [row[1] for row in cursor.fetchall()]

        if "incident_duration_minutes" not in pair_columns:
            logger.info(
                "Migrating database: Adding incident_duration_minutes to notification_pairs"
            )
            cursor.execute(
                "ALTER TABLE notification_pairs ADD COLUMN incident_duration_minutes INTEGER"
            )
            self.conn.commit()
            logger.info(
                "Migration complete: incident_duration_minutes added to notification_pairs"
            )

    def create_tables(self):
        """
        Public method to create database tables.
        Called by tests to explicitly initialize schema.
        This is safe to call multiple times (CREATE TABLE IF NOT EXISTS).
        """
        self._initialize_schema()

    # ==================== Notification Operations ====================

    def insert_notification(self, data: Dict) -> Optional[int]:
        """
        Insert a new notification into the database.

        Args:
            data: Dictionary with notification fields

        Returns:
            Notification ID if successful, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO notifications (
                    reference_number, gmail_message_id, thread_id, inbox_source,
                    date_received, time_received, platform, event_type, status, priority,
                    scheduled_date, scheduled_time, duration, affected_services, summary,
                    raw_email_body, raw_email_subject,
                    incident_start_time, incident_end_time, incident_duration_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.get("reference_number"),
                    data.get("gmail_message_id"),
                    data.get("thread_id"),
                    data.get("inbox_source"),
                    data.get("date_received"),
                    data.get("time_received"),
                    data.get("platform"),
                    data.get("event_type"),
                    data.get("status", "Open"),
                    data.get("priority", "Medium"),
                    data.get("scheduled_date"),
                    data.get("scheduled_time"),
                    data.get("duration"),
                    data.get("affected_services"),
                    data.get("summary"),
                    data.get("raw_email_body"),
                    data.get("raw_email_subject"),
                    data.get("incident_start_time"),
                    data.get("incident_end_time"),
                    data.get("incident_duration_minutes"),
                ),
            )
            self.conn.commit()
            logger.info(f"Inserted notification: {data.get('reference_number')}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logger.warning(
                f"Duplicate notification: {data.get('reference_number')} - {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Error inserting notification: {e}")
            return None

    def get_notification_by_reference(self, reference_number: str) -> Optional[Dict]:
        """Get notification by reference number"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE reference_number = ?",
            (reference_number,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_notification_by_gmail_id(self, gmail_message_id: str) -> Optional[Dict]:
        """Get notification by Gmail message ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE gmail_message_id = ?",
            (gmail_message_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_notifications(self, include_archived: bool = False) -> List[Dict]:
        """Get all notifications"""
        cursor = self.conn.cursor()
        if include_archived:
            cursor.execute("SELECT * FROM notifications ORDER BY date_received DESC")
        else:
            cursor.execute(
                "SELECT * FROM notifications WHERE is_archived = 0 ORDER BY date_received DESC"
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_notifications_by_status(
        self, status: str, include_archived: bool = False
    ) -> List[Dict]:
        """Get notifications by status"""
        cursor = self.conn.cursor()
        if include_archived:
            cursor.execute(
                "SELECT * FROM notifications WHERE status = ? ORDER BY date_received DESC",
                (status,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM notifications
                WHERE status = ? AND is_archived = 0
                ORDER BY date_received DESC
            """,
                (status,),
            )
        return [dict(row) for row in cursor.fetchall()]

    def update_notification(self, reference_number: str, updates: Dict) -> bool:
        """Update notification fields"""
        try:
            updates["last_updated"] = datetime.now().isoformat()
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [reference_number]

            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                UPDATE notifications
                SET {set_clause}
                WHERE reference_number = ?
            """,
                values,
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating notification {reference_number}: {e}")
            return False

    # ==================== Pairing Operations ====================

    def link_notification_pair(self, reference_number: str) -> bool:
        """
        Link Open and Resolved notifications for a reference number.
        Calculate resolution time.
        """
        try:
            cursor = self.conn.cursor()

            # Get Open and Resolved notifications (including incident duration)
            cursor.execute(
                """
                SELECT id, date_received, time_received, status, incident_duration_minutes
                FROM notifications
                WHERE reference_number = ?
                ORDER BY date_received
            """,
                (reference_number,),
            )

            notifications = cursor.fetchall()

            if len(notifications) < 2:
                return False

            open_notif = None
            resolved_notif = None

            for notif in notifications:
                if notif["status"] == "Open" and not open_notif:
                    open_notif = notif
                elif notif["status"] == "Resolved" and not resolved_notif:
                    resolved_notif = notif

            if not (open_notif and resolved_notif):
                return False

            # Calculate email processing time (time from open notification to resolved notification)
            open_dt = datetime.fromisoformat(open_notif["date_received"])
            resolved_dt = datetime.fromisoformat(resolved_notif["date_received"])
            time_to_resolve = int(
                (resolved_dt - open_dt).total_seconds() / 60
            )  # minutes

            # Get incident duration from resolved notification (if available)
            incident_duration = resolved_notif["incident_duration_minutes"]

            # Insert/update pair with both email processing time and incident duration
            cursor.execute(
                """
                INSERT OR REPLACE INTO notification_pairs
                (reference_number, open_notification_id, resolved_notification_id,
                 time_to_resolve_minutes, incident_duration_minutes)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    reference_number,
                    open_notif["id"],
                    resolved_notif["id"],
                    time_to_resolve,
                    incident_duration,
                ),
            )

            # Update resolved notification
            cursor.execute(
                """
                UPDATE notifications
                SET resolution_date = ?, time_to_resolve_minutes = ?
                WHERE id = ?
            """,
                (resolved_dt.isoformat(), time_to_resolve, resolved_notif["id"]),
            )

            # Mark ALL Open/Continuing notifications as Resolved (Resolved is final state)
            cursor.execute(
                """
                UPDATE notifications
                SET status = 'Resolved'
                WHERE reference_number = ?
                AND status IN ('Open', 'Continuing')
            """,
                (reference_number,),
            )

            self.conn.commit()
            logger.info(f"Linked pair {reference_number}: {time_to_resolve} minutes")
            return True

        except Exception as e:
            logger.error(f"Error linking pair {reference_number}: {e}")
            return False

    def get_notification_pairs(self) -> List[Dict]:
        """Get all notification pairs"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM notification_pairs
            ORDER BY id DESC
        """
        )
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Stats Operations ====================

    def get_current_stats(self, include_archived: bool = False) -> Dict:
        """Get current statistics"""
        cursor = self.conn.cursor()

        where_clause = "" if include_archived else "WHERE is_archived = 0"

        # Total counts
        cursor.execute(f"SELECT COUNT(*) as total FROM notifications {where_clause}")
        total = cursor.fetchone()["total"]

        # Status breakdown
        cursor.execute(
            f"""
            SELECT status, COUNT(*) as count
            FROM notifications {where_clause}
            GROUP BY status
        """
        )
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Platform breakdown
        cursor.execute(
            f"""
            SELECT platform, COUNT(*) as count
            FROM notifications {where_clause}
            GROUP BY platform
        """
        )
        platform_counts = {row["platform"]: row["count"] for row in cursor.fetchall()}

        # Event type breakdown
        cursor.execute(
            f"""
            SELECT event_type, COUNT(*) as count
            FROM notifications {where_clause}
            GROUP BY event_type
        """
        )
        event_counts = {row["event_type"]: row["count"] for row in cursor.fetchall()}

        # Average email processing time (time from open email to resolved email)
        cursor.execute(
            f"""
            SELECT AVG(time_to_resolve_minutes) as avg_time
            FROM notifications
            WHERE time_to_resolve_minutes IS NOT NULL
            {("AND is_archived = 0" if not include_archived else "")}
        """
        )
        avg_resolution = cursor.fetchone()["avg_time"] or 0

        # Average incident duration (actual outage time from resolved email)
        cursor.execute(
            f"""
            SELECT AVG(incident_duration_minutes) as avg_incident
            FROM notifications
            WHERE incident_duration_minutes IS NOT NULL AND status = 'Resolved'
            {("AND is_archived = 0" if not include_archived else "")}
        """
        )
        avg_incident = cursor.fetchone()["avg_incident"] or 0

        # Incident duration by platform (network breakdown)
        cursor.execute(
            f"""
            SELECT
                platform,
                COUNT(*) as count,
                AVG(incident_duration_minutes) as avg_duration,
                SUM(incident_duration_minutes) as total_duration
            FROM notifications
            WHERE incident_duration_minutes IS NOT NULL AND status = 'Resolved'
            {("AND is_archived = 0" if not include_archived else "")}
            GROUP BY platform
        """
        )
        platform_incident_stats = {
            row["platform"]: {
                "count": row["count"],
                "avg_duration": round(row["avg_duration"], 2)
                if row["avg_duration"]
                else 0,
                "total_duration": row["total_duration"] or 0,
            }
            for row in cursor.fetchall()
        }

        # Truly open issues count (exclude reference numbers that have been resolved)
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT reference_number) as count
            FROM notifications
            WHERE status IN ('Open', 'Continuing')
            {("AND is_archived = 0" if not include_archived else "")}
            AND reference_number NOT IN (
                SELECT reference_number
                FROM notifications
                WHERE status = 'Resolved'
            )
        """
        )
        truly_open_count = cursor.fetchone()["count"]

        return {
            "total_notifications": total,
            "open_count": truly_open_count,
            "resolved_count": status_counts.get("Resolved", 0),
            "continuing_count": status_counts.get("Continuing", 0),
            "platform_breakdown": platform_counts,
            "platform_incident_stats": platform_incident_stats,
            "event_type_breakdown": event_counts,
            "avg_resolution_time_minutes": round(avg_resolution, 2),
            "avg_incident_duration_minutes": round(avg_incident, 2),
        }

    def save_stats_snapshot(self) -> bool:
        """Save current stats as a snapshot"""
        try:
            stats = self.get_current_stats(include_archived=False)
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO stats_snapshots (
                    total_notifications, open_count, resolved_count, continuing_count,
                    avg_resolution_time_minutes, platform_breakdown, event_type_breakdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    stats["total_notifications"],
                    stats["open_count"],
                    stats["resolved_count"],
                    stats["continuing_count"],
                    stats["avg_resolution_time_minutes"],
                    json.dumps(stats["platform_breakdown"]),
                    json.dumps(stats["event_type_breakdown"]),
                ),
            )
            self.conn.commit()
            logger.info("Stats snapshot saved")
            return True
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            return False

    def get_historical_stats(self, days: int = 30) -> List[Dict]:
        """Get historical stats snapshots"""
        cursor = self.conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute(
            """
            SELECT * FROM stats_snapshots
            WHERE snapshot_date >= ?
            ORDER BY snapshot_date
        """,
            (since_date,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Archive Operations ====================

    def archive_old_notifications(self, days: int = 180) -> int:
        """Archive notifications older than specified days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET is_archived = 1
                WHERE date_received < ? AND is_archived = 0
            """,
                (cutoff_date,),
            )
            self.conn.commit()
            archived_count = cursor.rowcount
            logger.info(
                f"Archived {archived_count} notifications older than {days} days"
            )
            return archived_count
        except Exception as e:
            logger.error(f"Error archiving notifications: {e}")
            return 0

    def get_archived_notifications(self) -> List[Dict]:
        """Get all archived notifications"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE is_archived = 1 ORDER BY date_received DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Sync Operations ====================

    def log_sync_start(self, inbox_source: str) -> int:
        """Log start of sync operation"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sync_history (inbox_source, sync_start)
            VALUES (?, CURRENT_TIMESTAMP)
        """,
            (inbox_source,),
        )
        self.conn.commit()
        return cursor.lastrowid

    def log_sync_complete(
        self,
        sync_id: int,
        emails_fetched: int,
        emails_parsed: int,
        errors_count: int,
        status: str,
        error_log: str = None,
    ):
        """Log completion of sync operation"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE sync_history
            SET sync_end = CURRENT_TIMESTAMP,
                emails_fetched = ?,
                emails_parsed = ?,
                errors_count = ?,
                status = ?,
                error_log = ?
            WHERE id = ?
        """,
            (emails_fetched, emails_parsed, errors_count, status, error_log, sync_id),
        )
        self.conn.commit()

    def get_last_sync_date(self, inbox_source: str = None) -> Optional[datetime]:
        """Get date of last successful sync"""
        cursor = self.conn.cursor()
        if inbox_source:
            cursor.execute(
                """
                SELECT sync_start FROM sync_history
                WHERE inbox_source = ? AND status = 'success'
                ORDER BY sync_start DESC LIMIT 1
            """,
                (inbox_source,),
            )
        else:
            cursor.execute(
                """
                SELECT sync_start FROM sync_history
                WHERE status = 'success'
                ORDER BY sync_start DESC LIMIT 1
            """
            )
        row = cursor.fetchone()
        return datetime.fromisoformat(row["sync_start"]) if row else None

    def get_sync_history(self, limit: int = 10) -> List[Dict]:
        """Get recent sync history"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM sync_history
            ORDER BY sync_start DESC
            LIMIT ?
        """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Config Operations ====================

    def get_config(self, key: str, default=None):
        """Get configuration value"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

    def set_config(self, key: str, value: str):
        """Set configuration value"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
            (key, value),
        )
        self.conn.commit()

    # ==================== Utility Operations ====================

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def backup(self, backup_path: str = None):
        """Create database backup"""
        if backup_path is None:
            backup_path = (
                f"{self.db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

        import shutil

        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        return backup_path

    def vacuum(self):
        """Optimize database"""
        self.conn.execute("VACUUM")
        logger.info("Database vacuumed")
