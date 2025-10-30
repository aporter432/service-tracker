#!/usr/bin/env python3
"""
ORBCOMM Notification Processor - Interactive Version
Process ORBCOMM service notifications from various sources
"""

import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleORBCOMMParser:
    """Simplified parser for ORBCOMM notifications."""

    def __init__(self):
        self.data = []
        self.reference_counter = {}

    def parse_text(
        self, text: str, subject: str = "", email_date: str = None
    ) -> Dict:  # noqa: C901
        """Parse notification text and extract key information.

        Args:
            text: Email body text
            subject: Email subject line
            email_date: Optional email date string (RFC 2822 format from Gmail headers)
        """

        # Parse email date if provided
        if email_date:
            try:
                # Parse Gmail date format (RFC 2822)
                # Example: "Tue, 29 Oct 2024 10:30:45 -0700"
                from email.utils import parsedate_to_datetime

                dt = parsedate_to_datetime(email_date)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
            except Exception:
                # Fallback to current time if parsing fails
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H:%M")
        else:
            # Use current time as fallback
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H:%M")

        # Initialize result
        result = {
            "reference_number": "",
            "date_received": date_str,
            "time_received": time_str,
            "platform": "",
            "event_type": "",
            "status": "Open",
            "summary": "",
            "scheduled_date": "",
            "scheduled_time": "",
            "duration": "",
            "affected_services": "",
            "subject": subject,
            "incident_start_time": None,
            "incident_end_time": None,
            "incident_duration_minutes": None,
        }

        # Extract from subject line if provided
        if subject:
            # Look for reference number
            ref_match = re.search(r"([A-Z]-\d{6})", subject)
            if ref_match:
                result["reference_number"] = ref_match.group(1)

            # Determine status
            if any(
                word in subject.lower()
                for word in ["resolved", "completed", "restored"]
            ):
                result["status"] = "Resolved"
            elif "open" in subject.lower():
                result["status"] = "Open"
            elif "continuing" in subject.lower():
                result["status"] = "Continuing"

            # Extract platform from subject
            if "IDP" in subject:
                result["platform"] = "IDP"
            elif "OGx" in subject or "OGX" in subject:
                result["platform"] = "OGx"
            elif "OGWS" in subject:
                result["platform"] = "OGWS"

        # Parse the body text
        lines = text.split("\n")
        for line in lines:
            line = line.strip()

            # Platform
            if line.lower().startswith("platform:"):
                result["platform"] = line.split(":", 1)[1].strip()

            # Event
            elif line.lower().startswith("event:"):
                result["event_type"] = line.split(":", 1)[1].strip()

            # Summary
            elif line.lower().startswith("summary:"):
                # Get everything after "Summary:"
                summary_start = text.lower().find("summary:")
                if summary_start != -1:
                    result["summary"] = text[summary_start + 8 :].strip()

                    # Extract date and time from summary
                    summary_text = result["summary"]

                    # Look for date patterns (e.g., "November 5th", "Nov 5", "11/5")
                    date_patterns = [
                        r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?)",  # November 5th
                        r"(\d{1,2}/\d{1,2}/\d{4})",  # 11/5/2024
                        r"(\d{4}-\d{2}-\d{2})",  # 2024-11-05
                    ]

                    for pattern in date_patterns:
                        date_match = re.search(pattern, summary_text)
                        if date_match:
                            result["scheduled_date"] = date_match.group(1)
                            break

                    # Look for time patterns (e.g., "15:00 UTC", "3:00 PM")
                    time_match = re.search(
                        r"(\d{1,2}:\d{2}\s*(?:UTC|GMT|EST|PST|[AP]M)?)", summary_text
                    )
                    if time_match:
                        result["scheduled_time"] = time_match.group(1)

                    # Look for duration
                    duration_match = re.search(
                        r"(?:last|duration|take|approximately)\s+(\d+)\s+(hour|minute|day)s?",
                        summary_text,
                        re.IGNORECASE,
                    )
                    if duration_match:
                        result[
                            "duration"
                        ] = f"{duration_match.group(1)} {duration_match.group(2)}(s)"

                    # Extract affected services
                    services = []
                    service_keywords = [
                        "Partner-Support",
                        "VAPP",
                        "OGWS",
                        "Gateway",
                        "API",
                        "Portal",
                        "satellite",
                        "modem",
                    ]
                    for keyword in service_keywords:
                        if keyword.lower() in summary_text.lower():
                            services.append(keyword)
                    result["affected_services"] = "; ".join(services)

        # Extract incident Start Time and End Time from resolved emails
        # These are found in HTML format: <b>Start Time:</b>&nbsp;2025-10-22 15:05 GMT
        if result["status"] == "Resolved":
            ref_num = result.get("reference_number", "UNKNOWN")

            # Look for Start Time in HTML body
            start_match = re.search(r"<b>Start Time:</b>\s*&nbsp;([^<]+)", text)
            if start_match:
                start_time_str = start_match.group(1).strip()
                try:
                    # Parse format: "2025-10-22 15:05 GMT"
                    start_dt = datetime.strptime(
                        start_time_str.replace(" GMT", ""), "%Y-%m-%d %H:%M"
                    )
                    result["incident_start_time"] = start_dt.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    logger.debug(
                        f"[{ref_num}] Parsed incident start time: {result['incident_start_time']}"
                    )
                except Exception as e:
                    # If parsing fails, leave as None
                    logger.warning(
                        f"[{ref_num}] Failed to parse incident start time '{start_time_str}': {e}"
                    )
                    pass
            else:
                logger.debug(
                    f"[{ref_num}] No incident start time found in resolved notification (older format)"
                )

            # Look for End Time in HTML body
            end_match = re.search(r"<b>End Time:</b>\s*&nbsp;([^<]+)", text)
            if end_match:
                end_time_str = end_match.group(1).strip()
                try:
                    # Parse format: "2025-10-22 15:05 GMT"
                    end_dt = datetime.strptime(
                        end_time_str.replace(" GMT", ""), "%Y-%m-%d %H:%M"
                    )
                    result["incident_end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                    logger.debug(
                        f"[{ref_num}] Parsed incident end time: {result['incident_end_time']}"
                    )
                except Exception as e:
                    # If parsing fails, leave as None
                    logger.warning(
                        f"[{ref_num}] Failed to parse incident end time '{end_time_str}': {e}"
                    )
                    pass
            else:
                logger.debug(
                    f"[{ref_num}] No incident end time found in resolved notification (older format)"
                )

            # Calculate incident duration if both times are available
            if result["incident_start_time"] and result["incident_end_time"]:
                try:
                    start_dt = datetime.strptime(
                        result["incident_start_time"], "%Y-%m-%d %H:%M:%S"
                    )
                    end_dt = datetime.strptime(
                        result["incident_end_time"], "%Y-%m-%d %H:%M:%S"
                    )
                    duration_delta = end_dt - start_dt
                    result["incident_duration_minutes"] = int(
                        duration_delta.total_seconds() / 60
                    )
                    logger.info(
                        f"[{ref_num}] Calculated incident duration: {result['incident_duration_minutes']} minutes"
                    )
                except Exception as e:
                    # If calculation fails, leave as None
                    logger.error(
                        f"[{ref_num}] Failed to calculate incident duration: {e}"
                    )
                    pass
            elif result["incident_start_time"] or result["incident_end_time"]:
                # One time is present but not both
                logger.warning(
                    f"[{ref_num}] Incomplete incident times - "  # noqa: E501
                    f"start: {result['incident_start_time']}, end: {result['incident_end_time']}"
                )

        return result

    def add_notification(self, text: str, subject: str = ""):
        """Add a notification to the dataset."""
        parsed = self.parse_text(text, subject)
        self.data.append(parsed)
        return parsed

    def process_email_list(self, email_list: List[Dict]):
        """Process a list of email dictionaries."""
        for email in email_list:
            subject = email.get("subject", "")
            body = email.get("body", "")
            self.add_notification(body, subject)

    def calculate_durations(self):
        """Calculate durations between Open and Resolved pairs."""
        # Group by reference number
        grouped = {}
        for notif in self.data:
            ref = notif.get("reference_number")
            if ref:
                if ref not in grouped:
                    grouped[ref] = []
                grouped[ref].append(notif)

        # Calculate durations for each group
        for ref, notifications in grouped.items():
            if len(notifications) >= 2:
                # Find open and resolved
                open_notif = None
                resolved_notif = None

                for n in notifications:
                    if n["status"] == "Open" and not open_notif:
                        open_notif = n
                    elif n["status"] == "Resolved" and not resolved_notif:
                        resolved_notif = n

                if open_notif and resolved_notif:
                    # Calculate duration (simplified - would need actual datetime parsing)
                    # For now, just mark that they're paired
                    open_notif["resolution_status"] = "Resolved"
                    resolved_notif["resolution_status"] = "Paired with Open"

    def export_to_csv(self, filename: str = "orbcomm_notifications.csv"):
        """Export data to CSV file."""
        if not self.data:
            print("No data to export")
            return

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
        ]

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in self.data:
                # Truncate summary for CSV
                if len(row.get("summary", "")) > 200:
                    row["summary"] = row["summary"][:197] + "..."

                writer.writerow({k: row.get(k, "") for k in fieldnames})

        print(f"✅ Exported {len(self.data)} notifications to {filename}")

    def display_summary(self):
        """Display a summary of processed notifications."""
        print("\n📊 ORBCOMM Notification Summary")
        print("=" * 60)
        print(f"Total Notifications: {len(self.data)}")

        # Count by status
        status_count = {}
        for notif in self.data:
            status = notif.get("status", "Unknown")
            status_count[status] = status_count.get(status, 0) + 1

        print("\nBy Status:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")

        # Count by platform
        platform_count = {}
        for notif in self.data:
            platform = notif.get("platform", "Unknown")
            if platform:
                platform_count[platform] = platform_count.get(platform, 0) + 1

        print("\nBy Platform:")
        for platform, count in platform_count.items():
            print(f"  {platform}: {count}")

        # Count by event type
        event_count = {}
        for notif in self.data:
            event = notif.get("event_type", "Unknown")
            if event:
                event_count[event] = event_count.get(event, 0) + 1

        print("\nBy Event Type:")
        for event, count in event_count.items():
            print(f"  {event}: {count}")

        print("=" * 60)


def interactive_mode():  # noqa: C901
    """Run the parser in interactive mode."""
    parser = SimpleORBCOMMParser()

    print("🚀 ORBCOMM Notification Parser - Interactive Mode")
    print("=" * 60)
    print("Options:")
    print("1. Paste notification text (type 'END' on a new line when done)")
    print("2. Load from file")
    print("3. Process sample data")
    print("4. Export current data to CSV")
    print("5. Show summary")
    print("6. Quit")
    print("=" * 60)

    while True:
        choice = input("\nSelect option (1-6): ").strip()

        if choice == "1":
            print(
                "\n📋 Paste the notification text below (type 'END' on a new line when done):"
            )
            subject = input("Subject line (optional, press Enter to skip): ").strip()

            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)

            text = "\n".join(lines)
            if text:
                result = parser.add_notification(text, subject)
                print(
                    f"\n✅ Added notification: {result.get('reference_number', 'No ref#')} - "  # noqa: E501
                    f"{result.get('event_type', 'Unknown event')}"
                )

        elif choice == "2":
            filename = input("Enter filename: ").strip()
            if Path(filename).exists():
                with open(filename, "r") as f:
                    content = f.read()
                result = parser.add_notification(content)
                print(f"✅ Loaded and parsed file: {filename}")
            else:
                print(f"❌ File not found: {filename}")

        elif choice == "3":
            # Add sample data
            sample_notifications = [
                {
                    "subject": "ORBCOMM Service Notification: IDP-Maintenance (Reference#: M-003147)-Open",
                    "body": """Platform: IDP
Event: Maintenance
Summary: Dear ORBCOMM Partner, We will be conducting scheduled maintenance of the Partner-Support page and VAPP interface on November 5th at 15:00 UTC. The maintenance window is expected to last 1 hour.""",  # noqa: E501
                },
                {
                    "subject": "ORBCOMM Service Notification: IDP-System Performance (Reference#: S-003141)-Open",
                    "body": """Platform: IDP
Event: System Performance
Summary: Dear ORBCOMM Partner, We are currently experiencing system performance degradation affecting IDP services. Our team is investigating the issue.""",  # noqa: E501
                },
                {
                    "subject": "ORBCOMM Service Notification: IDP-System Performance (Reference#: S-003141)-Resolved",
                    "body": """Platform: IDP
Event: System Performance
Summary: Dear ORBCOMM Partner, The system performance issue has been resolved. All IDP services have been restored to normal operation.""",  # noqa: E501
                },
            ]

            for notif in sample_notifications:
                parser.add_notification(notif["body"], notif["subject"])

            print(f"✅ Added {len(sample_notifications)} sample notifications")

        elif choice == "4":
            filename = input(
                "Enter output filename (default: orbcomm_notifications.csv): "
            ).strip()
            if not filename:
                filename = "orbcomm_notifications.csv"
            parser.export_to_csv(filename)

        elif choice == "5":
            parser.display_summary()

        elif choice == "6":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid option. Please select 1-6.")


if __name__ == "__main__":
    # Check if running with arguments or interactive
    if len(sys.argv) > 1:
        # File mode
        parser = SimpleORBCOMMParser()
        for filename in sys.argv[1:]:
            if Path(filename).exists():
                with open(filename, "r") as f:
                    content = f.read()
                parser.add_notification(content)
                print(f"Processed: {filename}")

        parser.calculate_durations()
        parser.export_to_csv()
        parser.display_summary()
    else:
        # Interactive mode
        interactive_mode()
