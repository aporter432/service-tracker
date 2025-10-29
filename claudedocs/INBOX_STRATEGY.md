# Dual Inbox Strategy

## Configuration Overview

### Inbox 1: Historical Archive (One-Time Pull)
- **Type**: Personal Gmail with historical ORBCOMM notifications
- **Strategy**: One-time complete import of all historical emails
- **After Import**: Disabled, no ongoing monitoring
- **Purpose**: Load historical data for analytics and baseline

### Inbox 2: Continuous Monitoring (Daily Sync)
- **Type**: Google Workspace email (company domain)
- **Strategy**: Daily incremental sync (only new emails)
- **Purpose**: Ongoing service notification tracking

---

## Setup Process

### Phase 1: Historical Import (Inbox 1)

**Step 1: Authenticate Personal Gmail**
```bash
./venv/bin/python3 setup_gmail_auth.py --inbox 1 --email personal-email@gmail.com
```

**Step 2: Import All Historical Emails**
```bash
./venv/bin/python3 import_historical.py --inbox 1
```

This will:
- Fetch ALL ORBCOMM emails from inbox 1 (no date limit)
- Parse and store in database
- Mark inbox 1 as "historical_import_complete"
- Disable inbox 1 for future syncs

**Expected:** Could be 100-1000+ emails depending on history

---

### Phase 2: Continuous Monitoring (Inbox 2)

**Step 1: Set Up Google Workspace OAuth**

Google Workspace requires special OAuth setup:

1. **Google Cloud Console** (same project):
   - OAuth consent screen: Choose **"Internal"** if you have Workspace admin access
   - OR keep **"External"** and add workspace email as test user

2. **Workspace Admin** (if using Internal):
   - No extra steps needed if you're admin
   - If not admin, have admin approve the OAuth app

**Step 2: Authenticate Workspace Email**
```bash
./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email work-email@yourcompany.com
```

**Step 3: Initial Sync**
```bash
./venv/bin/python3 orbcomm_sync.py --inbox 2
```

This will:
- Fetch ORBCOMM emails from last 30 days (configurable)
- Parse and store in database
- Set up for daily incremental sync

---

## Configuration File

`~/.orbcomm/config.yaml` will be created:

```yaml
gmail:
  inboxes:
    - id: 1
      name: "Historical Archive"
      email: "personal-email@gmail.com"
      type: "personal"
      mode: "historical"
      enabled: false                    # Disabled after import
      historical_import_complete: true
      credentials_file: "~/.orbcomm/inbox1/credentials.json"
      token_file: "~/.orbcomm/inbox1/token.json"

    - id: 2
      name: "Production Monitoring"
      email: "work-email@yourcompany.com"
      type: "workspace"
      mode: "continuous"
      enabled: true                     # Active monitoring
      credentials_file: "~/.orbcomm/inbox2/credentials.json"
      token_file: "~/.orbcomm/inbox2/token.json"

  search_query: 'subject:"ORBCOMM Service Notification:"'

sync:
  interval_hours: 24                    # Daily sync
  auto_start: false
  continuous_inbox: 2                   # Only sync inbox 2

database:
  path: "~/.orbcomm/tracker.db"

archive:
  enabled: true
  archive_after_days: 180
```

---

## Import Process Flow

### Historical Import (One-Time)
```
1. Authenticate Inbox 1 (personal Gmail)
2. Run: import_historical.py --inbox 1
   ├─ Fetch ALL emails (no date filter)
   ├─ Progress: 0/847 emails...
   ├─ Parse each email
   ├─ Store in database (inbox_source='inbox1_historical')
   ├─ Link Open/Resolved pairs
   └─ Mark complete
3. Inbox 1 disabled automatically
4. Result: Complete historical data loaded
```

### Continuous Sync (Daily)
```
1. Authenticate Inbox 2 (Google Workspace)
2. Initial sync: Last 30 days
3. Daily sync (automated):
   ├─ Check last_sync_date (from database)
   ├─ Fetch emails since last_sync_date
   ├─ Parse new emails only
   ├─ Store in database (inbox_source='inbox2_continuous')
   └─ Update last_sync_date
4. Result: Always up to date
```

---

## Database Tracking

Each notification will have:
- `inbox_source`:
  - `"inbox1_historical"` - From historical import
  - `"inbox2_continuous"` - From ongoing monitoring

This allows you to:
- Filter by source in dashboard
- See historical trends vs current monitoring
- Track which inbox notifications came from

---

## Sync Schedule

**After initial setup:**

```bash
# Manual sync anytime:
./venv/bin/python3 orbcomm_sync.py

# Or schedule daily (macOS launchd):
python3 setup_scheduler.py --daily 09:00
```

**Scheduler will:**
- Only sync inbox 2 (continuous monitoring)
- Run once per day
- Archive old notifications (>180 days)
- Save stats snapshots

---

## Google Workspace Considerations

### OAuth Consent Screen Options:

**Option A: Internal (Best if you're Workspace admin)**
- Simpler: No "unverified app" warnings
- Only works within your organization
- Requires Workspace admin to configure

**Option B: External (If not admin)**
- Works with any Workspace account
- Shows "unverified app" warning (click "Advanced" → "Go to...")
- Add your work email as test user
- Safe: It's your own app

### Permissions Required:
- `https://www.googleapis.com/auth/gmail.readonly`
- Read-only access to Gmail
- No send, delete, or modify permissions

---

## Benefits of This Approach

### Efficiency:
- Historical inbox: Pull once, never again
- Active inbox: Only fetch new emails daily
- No redundant API calls

### Cost:
- Gmail API quota: 1 billion units/day
- Historical import: ~1000 emails = minimal usage
- Daily sync: <100 emails = negligible usage

### Clarity:
- Historical data preserved
- Current monitoring separate
- Easy to see data source in dashboard

---

## Timeline

**Total setup time: 15-30 minutes**

1. **Gmail API Setup**: 10 minutes
   - Create project, enable API, get credentials

2. **Historical Import**: 5-10 minutes
   - Authenticate inbox 1
   - Import all emails (depends on count)

3. **Workspace Setup**: 5-10 minutes
   - Authenticate inbox 2
   - Initial sync

4. **Dashboard**: Instant
   - View all data
   - See historical + current

---

## Next Steps

Ready to proceed? Here's the order:

1. **Get OAuth credentials** (both inboxes use same credentials.json)
2. **Import historical** (inbox 1)
3. **Set up continuous** (inbox 2)
4. **Launch dashboard**

Let me know when you're ready for step 1!
