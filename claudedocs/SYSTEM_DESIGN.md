# ORBCOMM Service Tracker - System Design Specification

## Executive Summary

Transform the ORBCOMM email parser into an automated tracking system with Gmail integration, persistent storage, historical analytics, and automated synchronization.

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Web Dashboard│  Mac GUI App │  CLI Tool    │  API Endpoints │
└──────┬────────┴──────┬───────┴──────┬───────┴────────┬───────┘
       │               │              │                │
       └───────────────┴──────────────┴────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │     APPLICATION CORE              │
         │  ┌─────────────────────────────┐ │
         │  │  Service Orchestrator       │ │
         │  └─────────────────────────────┘ │
         │                                   │
         │  ┌────────────┬──────────────┐  │
         │  │  Parser    │  Analytics   │  │
         │  │  Engine    │  Engine      │  │
         │  └────────────┴──────────────┘  │
         └─────────────────┴─────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       │                                        │
┌──────▼────────┐  ┌──────────────┐  ┌────────▼────────┐
│ Gmail API     │  │ Notification │  │ SQLite Database │
│ Integration   │  │ System       │  │ (Persistence)   │
└───────────────┘  └──────────────┘  └─────────────────┘
```

---

## Layer Specifications

### 1. Data Layer (Persistence)

**Database: SQLite** (File-based, zero-config, perfect for local deployment)

**Schema Design:**

```sql
-- Core notifications table
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number TEXT UNIQUE NOT NULL,
    gmail_message_id TEXT UNIQUE,
    thread_id TEXT,

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

    -- Metadata
    is_archived BOOLEAN DEFAULT 0,
    notes TEXT,

    FOREIGN KEY (reference_number) REFERENCES notification_pairs(reference_number)
);

-- Track open/resolved pairs for accurate timing
CREATE TABLE notification_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number TEXT UNIQUE NOT NULL,
    open_notification_id INTEGER,
    resolved_notification_id INTEGER,
    time_to_resolve_minutes INTEGER,

    FOREIGN KEY (open_notification_id) REFERENCES notifications(id),
    FOREIGN KEY (resolved_notification_id) REFERENCES notifications(id)
);

-- Historical stats snapshots (for trend analysis)
CREATE TABLE stats_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_notifications INTEGER,
    open_count INTEGER,
    resolved_count INTEGER,
    continuing_count INTEGER,
    avg_resolution_time_minutes REAL,
    platform_breakdown TEXT,  -- JSON string
    event_type_breakdown TEXT  -- JSON string
);

-- Email sync tracking
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    sync_end DATETIME,
    emails_fetched INTEGER,
    emails_parsed INTEGER,
    errors_count INTEGER,
    last_email_date DATETIME,
    status TEXT CHECK(status IN ('success', 'partial', 'failed')),
    error_log TEXT
);

-- User preferences/config
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notifications_reference ON notifications(reference_number);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_date ON notifications(date_received);
CREATE INDEX idx_notifications_platform ON notifications(platform);
CREATE INDEX idx_notifications_gmail_id ON notifications(gmail_message_id);
CREATE INDEX idx_sync_history_date ON sync_history(sync_start);
```

**Key Design Decisions:**
- **SQLite over PostgreSQL/MySQL**: Zero setup, file-based, perfect for single-user local deployment
- **notification_pairs table**: Enables accurate resolution time calculation by linking Open → Resolved
- **stats_snapshots**: Periodic snapshots enable historical trend analysis without recalculating
- **sync_history**: Audit trail of Gmail sync operations for debugging and reliability

---

### 2. Gmail Integration Layer

**Technology Stack:**
- **Google Gmail API** (official Python client: `google-api-python-client`)
- **OAuth 2.0** for secure authentication
- **Background sync** with configurable intervals

**Architecture Pattern: Repository Pattern**

```python
class GmailRepository:
    """Handles all Gmail API interactions"""

    def authenticate() -> Credentials
    def fetch_orbcomm_emails(since_date: datetime) -> List[Message]
    def mark_as_processed(message_id: str) -> bool
    def get_email_content(message_id: str) -> EmailContent
    def batch_fetch_emails(message_ids: List[str]) -> List[EmailContent]
```

**API Query Strategy:**

```python
# Gmail API search query
query = 'subject:"ORBCOMM Service Notification:" newer_than:7d'

# Incremental sync: only fetch new emails since last sync
last_sync_date = get_last_sync_date()
query = f'subject:"ORBCOMM Service Notification:" after:{last_sync_date}'
```

**Features:**
1. **Incremental Sync**: Only fetch emails since last successful sync
2. **Batch Processing**: Fetch multiple emails in single API call (performance)
3. **Error Recovery**: Retry failed fetches with exponential backoff
4. **Deduplication**: Check gmail_message_id before inserting to prevent duplicates
5. **Thread Tracking**: Store thread_id to link related notifications

**Rate Limiting & Quotas:**
- Gmail API: 1 billion quota units/day (typically sufficient)
- Batch requests: Up to 100 emails per batch
- Implement exponential backoff for rate limit errors

---

### 3. Parser Engine (Enhanced)

**Reuse existing parser with enhancements:**

```python
class EnhancedORBCOMMParser(SimpleORBCOMMParser):
    """Enhanced parser with database integration"""

    def parse_and_store(email: EmailContent, db: DatabaseConnection) -> Notification
    def link_open_resolved_pair(ref_number: str, db: DatabaseConnection) -> bool
    def calculate_resolution_time(open_notif: Notification, resolved_notif: Notification) -> int
    def extract_priority(event_type: str, summary: str) -> str
```

**Enhanced Parsing Features:**
1. **Priority Detection**: Auto-assign priority based on keywords
   - "Critical", "Urgent", "Immediate" → High
   - "Performance", "Degradation", "Outage" → High
   - "Maintenance" → Medium
   - Default → Medium

2. **Smart Pairing**: Automatically link Open/Resolved notifications by reference number

3. **Duration Calculation**: When resolved notification arrives, calculate actual time to resolve

4. **Multi-format Support**: Handle various email formats (HTML, plain text, forwarded)

---

### 4. Analytics & Stats Engine

**Real-time Analytics:**

```python
class AnalyticsEngine:
    """Calculate stats and insights from notification data"""

    def get_current_stats() -> Dict[str, Any]:
        """Return current state statistics"""
        return {
            'total_notifications': count_all(),
            'open_issues': count_by_status('Open'),
            'resolved_issues': count_by_status('Resolved'),
            'platform_breakdown': group_by_platform(),
            'event_type_distribution': group_by_event_type(),
            'avg_resolution_time': calculate_avg_resolution_time(),
            'critical_open_issues': count_critical_open(),
        }

    def get_historical_trends(days: int = 30) -> Dict[str, Any]:
        """Analyze trends over time period"""
        return {
            'daily_notification_count': group_by_day(),
            'resolution_time_trend': resolution_times_by_week(),
            'platform_reliability': calculate_platform_mtbf(),
        }

    def generate_snapshot() -> None:
        """Save current stats to stats_snapshots table"""
        pass
```

**Key Metrics:**
- **MTTR** (Mean Time To Resolve): Average resolution time
- **Open Issue Age**: How long issues have been open
- **Platform Reliability**: Incidents per platform over time
- **Event Type Frequency**: Which event types occur most
- **Peak Incident Times**: When do most incidents occur

**Periodic Snapshot Strategy:**
- Save stats snapshot: Daily at midnight
- Retention: Keep daily snapshots for 90 days, weekly thereafter
- Enables trend analysis without recalculating historical data

---

### 5. Service Orchestrator

**Automation & Coordination Layer:**

```python
class ServiceOrchestrator:
    """Coordinate all system operations"""

    def sync_gmail() -> SyncResult:
        """Fetch, parse, store new emails"""
        1. Fetch emails from Gmail API
        2. Parse each email with EnhancedORBCOMMParser
        3. Store in database
        4. Link open/resolved pairs
        5. Update stats
        6. Log sync results

    def run_periodic_maintenance() -> None:
        """Daily maintenance tasks"""
        1. Generate stats snapshot
        2. Archive old resolved notifications (optional)
        3. Cleanup temp files
        4. Vacuum database

    def export_archive(date_range: tuple) -> str:
        """Export historical data to CSV/JSON"""
        pass
```

**Automation Options:**

**Option A: Manual Sync (Simplest)**
```bash
python orbcomm_sync.py --sync-now
```

**Option B: Scheduled Sync (macOS launchd)**
```bash
# Run every 15 minutes
python orbcomm_sync.py --daemon --interval 15m
```

**Option C: Always-On Service (Advanced)**
```bash
# Background service with web dashboard
python orbcomm_service.py --port 8080
```

---

### 6. User Interface Layer

**Three Interface Options:**

#### A. Enhanced CLI Tool
```bash
# Manual sync
$ python orbcomm_tracker.py sync

# View stats
$ python orbcomm_tracker.py stats

# View open issues
$ python orbcomm_tracker.py list --status open

# Export archive
$ python orbcomm_tracker.py export --format csv --range 30d
```

#### B. Web Dashboard (Recommended)
```
Flask/FastAPI + SQLite + Simple HTML/JS

Features:
- Real-time stats dashboard
- Notification list with filtering
- Historical charts (Chart.js)
- Manual sync trigger
- Export functionality
```

#### C. Enhanced Mac GUI
```
Extend orbcomm_mac_gui.py with:
- Gmail sync button
- Database browsing
- Stats visualization
- Historical view
```

---

## Implementation Phases

### Phase 1: Database Foundation (Day 1)
- [ ] Create SQLite schema
- [ ] Database migration script
- [ ] Basic CRUD operations
- [ ] Testing with sample data

### Phase 2: Gmail Integration (Day 2-3)
- [ ] Set up Gmail API credentials
- [ ] Implement OAuth flow
- [ ] Fetch emails functionality
- [ ] Incremental sync logic
- [ ] Deduplication handling

### Phase 3: Enhanced Parser (Day 3)
- [ ] Integrate parser with database
- [ ] Open/Resolved pairing logic
- [ ] Priority detection
- [ ] Resolution time calculation

### Phase 4: Analytics Engine (Day 4)
- [ ] Stats calculation functions
- [ ] Snapshot generation
- [ ] Historical trend analysis
- [ ] Export functionality

### Phase 5: Orchestration (Day 4-5)
- [ ] Service orchestrator
- [ ] Sync scheduling
- [ ] Error handling & retry logic
- [ ] Logging system

### Phase 6: UI Layer (Day 5-7)
- [ ] Choose: CLI / Web Dashboard / Enhanced GUI
- [ ] Implement interface
- [ ] Stats visualization
- [ ] Testing & refinement

---

## Technical Specifications

### Dependencies

```python
# Core
python >= 3.9

# Gmail Integration
google-auth >= 2.23.0
google-auth-oauthlib >= 1.1.0
google-api-python-client >= 2.100.0

# Database
sqlite3 (built-in)

# CLI (if chosen)
click >= 8.1.0
rich >= 13.0.0  # Beautiful terminal output

# Web Dashboard (if chosen)
flask >= 3.0.0
flask-cors >= 4.0.0

# Analytics & Visualization
pandas >= 2.0.0  # Optional: advanced analytics
plotly >= 5.17.0  # Optional: interactive charts

# Scheduling (if daemon mode)
schedule >= 1.2.0
apscheduler >= 3.10.0

# Utilities
python-dateutil >= 2.8.0
pytz >= 2023.3
```

### Configuration Management

**config.yaml**
```yaml
gmail:
  credentials_file: ~/.orbcomm/credentials.json
  token_file: ~/.orbcomm/token.json
  sync_interval_minutes: 15
  max_emails_per_sync: 100
  search_query: 'subject:"ORBCOMM Service Notification:"'

database:
  path: ~/.orbcomm/tracker.db
  backup_enabled: true
  backup_interval_days: 7

sync:
  auto_start: false
  retry_attempts: 3
  retry_delay_seconds: 60

stats:
  snapshot_enabled: true
  snapshot_time: "00:00"  # Midnight
  retention_days: 90

export:
  default_format: csv
  archive_path: ~/Documents/ORBCOMM_Archives

logging:
  level: INFO
  file: ~/.orbcomm/tracker.log
  max_size_mb: 10
  backup_count: 5
```

---

## Security Considerations

1. **OAuth 2.0 Credentials**: Store in secure location (`~/.orbcomm/`)
2. **Token Encryption**: Consider encrypting refresh tokens at rest
3. **API Key Protection**: Never commit credentials to git
4. **Database Access**: File-based SQLite with proper permissions (600)
5. **Input Validation**: Sanitize all email content before storage
6. **Rate Limiting**: Respect Gmail API quotas

---

## Deployment Strategy

### macOS Deployment (Recommended)

**Directory Structure:**
```
~/.orbcomm/
├── credentials.json       # Gmail OAuth credentials
├── token.json            # Refresh token (auto-generated)
├── tracker.db            # SQLite database
├── tracker.log           # Application logs
└── config.yaml           # User configuration

~/Projects/Service Tracker/
├── orbcomm_tracker/
│   ├── __init__.py
│   ├── database.py       # Database operations
│   ├── gmail_api.py      # Gmail integration
│   ├── parser.py         # Enhanced parser
│   ├── analytics.py      # Stats engine
│   ├── orchestrator.py   # Service coordinator
│   └── cli.py            # CLI interface
├── orbcomm_dashboard.py  # Web dashboard (optional)
├── orbcomm_sync.py       # Sync script
├── setup.py              # Installation script
└── requirements.txt      # Dependencies
```

**Installation:**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Initialize system
python3 setup.py init

# Authenticate with Gmail
python3 setup.py auth

# First sync
python3 orbcomm_sync.py --sync-now

# (Optional) Enable scheduled sync
python3 setup.py install-scheduler
```

---

## Performance Considerations

### Expected Performance

- **Initial Sync**: ~1-2 seconds per 100 emails
- **Incremental Sync**: <5 seconds for typical daily volume
- **Database Queries**: <50ms for typical stats queries
- **Stats Snapshot**: <1 second
- **Export**: ~1 second per 1000 notifications

### Optimization Strategies

1. **Batch Operations**: Fetch/insert multiple records at once
2. **Database Indexing**: Properly indexed for common queries
3. **Connection Pooling**: Reuse database connections
4. **Caching**: Cache frequently accessed stats (5-minute TTL)
5. **Async Processing**: Use async for Gmail API calls (optional)

---

## Monitoring & Observability

### Logging Strategy

```python
# Log levels by component
ERROR: Failed sync operations, database errors, API failures
WARN: Rate limiting, partial sync, missing data
INFO: Successful sync, stats snapshots, new notifications
DEBUG: Detailed parsing, API calls, database queries
```

### Health Checks

```python
def system_health_check() -> Dict[str, str]:
    return {
        'database': check_db_connection(),
        'gmail_api': check_gmail_auth(),
        'last_sync': get_last_sync_time(),
        'open_issues': count_open_issues(),
        'disk_space': check_disk_space(),
    }
```

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
- [ ] Email notifications for critical incidents
- [ ] Slack/Discord integration
- [ ] Mobile app (iOS/Android)
- [ ] Multi-user support with role-based access
- [ ] Advanced ML-based incident prediction
- [ ] Integration with ticketing systems (Jira, ServiceNow)
- [ ] Custom alert rules and thresholds
- [ ] API for external integrations

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gmail API quota exceeded | High | Implement rate limiting, batch requests |
| Database corruption | High | Daily backups, transaction handling |
| OAuth token expiration | Medium | Automatic refresh token handling |
| Email format changes | Medium | Robust parsing with fallbacks |
| Network connectivity loss | Low | Retry logic, queue failed syncs |
| Large database growth | Low | Archive old data, vacuum regularly |

---

## Success Metrics

### MVP Success Criteria
- ✅ Successfully authenticate with Gmail
- ✅ Fetch and parse 100% of ORBCOMM notifications
- ✅ Store notifications in database without duplicates
- ✅ Calculate resolution times accurately
- ✅ Generate real-time stats dashboard
- ✅ Export historical data to CSV
- ✅ Run automated sync every 15 minutes

### Performance Targets
- Sync latency: <10 seconds for typical volume
- Stats query time: <100ms
- Database size: <100MB for 1 year of data
- Uptime: >99% for scheduled syncs

---

## Next Steps

**Immediate Actions:**
1. Review and approve this design
2. Choose UI approach (CLI / Web / GUI)
3. Set up Gmail API credentials
4. Begin Phase 1 implementation

**Questions for User:**
1. **UI Preference**: CLI, Web Dashboard, or Enhanced GUI?
2. **Sync Frequency**: Every 15min, hourly, or manual?
3. **Archive Strategy**: Keep all data forever, or archive after 90 days?
4. **Notifications**: Want alerts for critical incidents?

---

## Conclusion

This design provides a robust, scalable foundation for automated ORBCOMM service tracking with Gmail integration, persistent storage, comprehensive analytics, and flexible automation options.

**Key Strengths:**
- Simple deployment (SQLite, file-based)
- Powerful analytics and historical tracking
- Flexible automation options
- Extensible architecture for future enhancements
- Production-ready error handling and logging

**Estimated Timeline:** 5-7 days for MVP with chosen UI option
