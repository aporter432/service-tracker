# ORBCOMM Service Tracker

Automated tracking system for ORBCOMM Service Notifications with Gmail integration, historical data analysis, and web dashboard.

## Features

- **Dual Inbox Strategy**: Historical archive (inbox 1) + continuous monitoring (inbox 2)
- **Automated Daily Sync**: Fetch new notifications every day at 9:00 AM
- **Notification Pairing**: Automatically links Open/Resolved notifications
- **Incident Duration Tracking**: Extracts actual incident start/end times from resolved emails for accurate outage measurements
- **Dual Metrics System**: Tracks both email processing time (notification delays) and actual incident duration (outage time)
- **Network Performance Analytics**: Platform-specific incident statistics (IDP, OGx, OGWS) for network comparison
- **Web Dashboard**: Real-time visualization of notifications and statistics
- **180-Day Archiving**: Automatic archival of old notifications
- **CSV Export**: Export notifications for external analysis

## System Architecture

```
ORBCOMM Service Notifications (Gmail)
    ↓
Gmail API Integration (OAuth 2.0 Read-Only)
    ↓
Parser (Email → Structured Data)
    ↓
SQLite Database (Local Storage)
    ↓
    ├→ Web Dashboard (Flask)
    ├→ Manual Sync (CLI)
    └→ Daily Scheduler (launchd)
```

## Quick Start

### 1. Start the Web Dashboard

```bash
cd ~/Projects/Service\ Tracker
./venv/bin/python3 orbcomm_dashboard.py
```

Then open your browser to: **http://127.0.0.1:5000**

### 2. Run Manual Sync

```bash
./venv/bin/python3 run_sync.py --inbox 2
```

### 3. Check Scheduler Status

```bash
./venv/bin/python3 setup_scheduler.py --status
```

## Project Structure

```
~/Projects/Service Tracker/
├── orbcomm_tracker/              # Core package
│   ├── __init__.py
│   ├── database.py               # SQLite database layer
│   ├── gmail_api.py              # Gmail API integration
│   ├── parser.py                 # Email parser
│   └── sync.py                   # Sync orchestrator
│
├── templates/                    # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── notifications.html
│   ├── notification_detail.html
│   ├── stats.html
│   └── error.html
│
├── static/                       # CSS/JS assets
│   └── style.css
│
├── venv/                         # Virtual environment
│
├── orbcomm_dashboard.py          # Web dashboard (Flask)
├── orbcomm_scheduler.py          # Daily automation script
├── run_sync.py                   # Manual sync CLI
├── setup_scheduler.py            # Scheduler install/uninstall
├── import_historical.py          # One-time historical import
├── backfill_incident_times.py    # Backfill incident durations from existing emails
├── setup_gmail_auth.py           # Gmail OAuth setup
├── test_gmail_connection.py      # Connection tester
│
└── requirements.txt              # Python dependencies

~/.orbcomm/                       # Data directory (outside project)
├── inbox1/                       # Personal Gmail auth
│   ├── credentials.json
│   └── token.json
├── inbox2/                       # Workspace Gmail auth
│   ├── credentials.json
│   └── token.json
├── logs/                         # Sync logs
│   ├── sync_YYYYMMDD.log
│   ├── scheduler_stdout.log
│   └── scheduler_stderr.log
└── tracker.db                    # SQLite database
```

## Current Database Stats

- **Total notifications**: 55
- **Open issues**: 4
- **Resolved**: 21
- **Avg email processing time**: 32.6 hours (notification system delay)
- **Avg incident duration**: 2.8 hours (actual outage time from resolved emails)
- **Network breakdown**: IDP (7 incidents, avg 4.2h), OGx (4 incidents, avg 0.3h)
- **Date range**: April 2025 - October 2025

### Incident Duration Feature

**New in v1.1.0**: The system now extracts actual incident start and end times directly from resolved notification emails, providing accurate outage duration measurements.

**Key Benefits**:
- **Accuracy**: Eliminated up to 167-hour errors caused by email notification delays
- **Dual Metrics**: Track both email processing time (32.6h avg) and actual incident duration (2.8h avg)
- **Network Insights**: Compare performance across IDP, OGx, and OGWS networks
- **SLA Tracking**: Accurate incident durations for service level compliance

**Technical Details**:
- Parses HTML email content to extract `<b>Start Time:</b>` and `<b>End Time:</b>` from resolved notifications
- Stores both timestamps and calculated duration in database
- Dashboard displays separate metrics for email processing vs incident duration
- Network breakdown shows platform-specific incident statistics
- Backward compatible with older notifications that lack incident times

## Usage Guide

### Web Dashboard

The dashboard provides:
- **Dashboard Page**: Overview stats, open issues, recent notifications
- **Notifications Page**: Full list with filtering (status, platform, archived)
- **Statistics Page**: Platform breakdown, event types, historical trends
- **Detail View**: Complete notification details with paired notifications
- **Manual Sync**: Trigger immediate sync via "Sync Now" button
- **CSV Export**: Export filtered notifications

**Available filters:**
- Status: All, Open, Resolved, Continuing
- Platform: All, IDP, OGx, OGWS
- Include archived notifications

### Manual Sync CLI

```bash
# Check status
./venv/bin/python3 run_sync.py --inbox 2 --status

# Run sync (auto-detects last sync date)
./venv/bin/python3 run_sync.py --inbox 2

# Sync last 30 days
./venv/bin/python3 run_sync.py --inbox 2 --days 30

# Sync + archive + snapshot
./venv/bin/python3 run_sync.py --inbox 2 --archive 180 --snapshot
```

### Daily Scheduler

**Installed and running:**
- **Schedule**: Every day at 9:00 AM
- **Tasks**: Fetch new emails, parse, store, link pairs, archive old, save snapshot, vacuum DB
- **Logs**: `~/.orbcomm/logs/`

**Management commands:**
```bash
# Check status
./venv/bin/python3 setup_scheduler.py --status

# Reinstall
./venv/bin/python3 setup_scheduler.py --uninstall
./venv/bin/python3 setup_scheduler.py --install

# View logs
tail -f ~/.orbcomm/logs/scheduler_stdout.log
tail -f ~/.orbcomm/logs/sync_$(date +%Y%m%d).log

# Check launchd
launchctl list | grep orbcomm
```

### Database Operations

```python
from orbcomm_tracker.database import Database

db = Database()

# Get current stats
stats = db.get_current_stats()
print(f"Total: {stats['total_notifications']}")
print(f"Open: {stats['open_count']}")

# Get open issues
open_issues = db.get_notifications_by_status('Open')

# Get notification by reference
notif = db.get_notification_by_reference('M-003147')

# Archive old notifications (manually)
archived = db.archive_old_notifications(days=180)

# Backup database
backup_path = db.backup()

db.close()
```

## Key Technical Decisions

1. **SQLite over PostgreSQL/MySQL**: Zero setup, file-based, perfect for single-user
2. **Dual inbox strategy**: Historical one-time import + continuous monitoring
3. **~/.orbcomm/ for data**: Standard Mac app pattern, separate code from data
4. **Virtual environment**: Isolated dependencies
5. **Flask for dashboard**: Simple, lightweight, Python-native
6. **launchd for scheduling**: Native macOS scheduling (vs cron)

## Security

- **OAuth 2.0**: Read-only Gmail access (`gmail.readonly` scope)
- **Credentials**: Stored in `~/.orbcomm/` (home directory)
- **No passwords**: Only OAuth refresh tokens
- **.gitignore**: Protects all sensitive files

## Development

### Dependencies

```
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
flask==3.0.0
```

### Adding New Features

1. **New database fields**: Update `orbcomm_tracker/database.py` schema
2. **New email parsing**: Update `orbcomm_processor.py`
3. **New dashboard pages**: Add template + route in `orbcomm_dashboard.py`
4. **New sync logic**: Update `orbcomm_tracker/sync.py`

## Troubleshooting

### Dashboard won't start
```bash
# Check if port 5000 is available
lsof -i :5000

# Try different port
./venv/bin/python3 orbcomm_dashboard.py --port 8000
```

### Scheduler not running
```bash
# Check launchd status
launchctl list | grep orbcomm

# Check logs for errors
cat ~/.orbcomm/logs/scheduler_stderr.log

# Reinstall
./venv/bin/python3 setup_scheduler.py --uninstall
./venv/bin/python3 setup_scheduler.py --install
```

### Gmail authentication expired
```bash
# Re-authenticate inbox
./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email aporter@pro-texis.com
```

### Database issues
```bash
# Backup first!
cp ~/.orbcomm/tracker.db ~/.orbcomm/tracker.db.backup

# Check database integrity
sqlite3 ~/.orbcomm/tracker.db "PRAGMA integrity_check;"

# Vacuum database
sqlite3 ~/.orbcomm/tracker.db "VACUUM;"
```

## Future Enhancements

- [ ] Email notifications for critical issues
- [ ] Slack/Teams integration
- [ ] Advanced analytics and charts
- [ ] Multi-user support with authentication
- [ ] Mobile-responsive dashboard improvements
- [ ] API endpoints for external integrations
- [ ] Notification templates and categorization
- [ ] SLA tracking and alerting

## Support

For issues or questions:
1. Check logs: `~/.orbcomm/logs/`
2. Review error messages in dashboard
3. Verify Gmail authentication is valid
4. Confirm scheduler is running

## License

Private project for Pro-Texis internal use.

---

**Last Updated**: October 29, 2025
**Version**: 1.1.0 - Incident Duration Tracking
**Status**: Production Ready ✅
