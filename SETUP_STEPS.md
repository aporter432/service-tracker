# ORBCOMM Tracker - Setup Steps

**Updated Strategy: Historical + Continuous Monitoring**

---

## 📋 Overview

- **Inbox 1** (Personal Gmail): One-time import of ALL historical emails → then disabled
- **Inbox 2** (Google Workspace): Daily monitoring of new emails → ongoing

---

## ✅ Step 1: Get Gmail API Credentials (10 min)

### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: **"ORBCOMM Tracker"**
3. Go to **APIs & Services** → **Library**
4. Search "Gmail API" → Enable it

### 1.2 OAuth Consent Screen
1. Go to **OAuth consent screen**
2. Choose **"External"** (works for both personal + Workspace)
3. App name: `ORBCOMM Service Tracker`
4. Add scope: `https://www.googleapis.com/auth/gmail.readonly`
5. Add test users:
   - Your personal Gmail
   - Your Google Workspace email (work@company.com)

### 1.3 Get Credentials
1. Go to **Credentials** → Create Credentials → OAuth client ID
2. Application type: **Desktop app**
3. Download JSON → save as `credentials.json`

### 1.4 Copy Credentials
```bash
# Create directories
mkdir -p ~/.orbcomm/inbox1
mkdir -p ~/.orbcomm/inbox2

# Copy credentials for both inboxes
cp ~/Downloads/credentials.json ~/.orbcomm/inbox1/
cp ~/Downloads/credentials.json ~/.orbcomm/inbox2/
```

---

## ✅ Step 2: Import Historical Emails (5-15 min)

### 2.1 Authenticate Personal Gmail (Inbox 1)
```bash
./venv/bin/python3 setup_gmail_auth.py \
  --inbox 1 \
  --email your-personal-email@gmail.com
```

**What happens:**
- Browser opens
- Sign in to your personal Gmail
- Grant permissions (click "Advanced" → "Go to..." if unverified warning)
- See "Authentication successful!"

### 2.2 Import All Historical Emails
```bash
./venv/bin/python3 import_historical.py --inbox 1
```

**What happens:**
- Searches for ALL ORBCOMM emails (no date limit)
- Shows progress: `[1/847] ✅ Imported: M-003147`
- Parses and stores each email
- Links Open/Resolved pairs
- Shows final stats
- Marks inbox 1 as complete (disabled for future syncs)

**Expected time:** 1-10 minutes depending on email count

---

## ✅ Step 3: Set Up Continuous Monitoring (5 min)

### 3.1 Authenticate Google Workspace (Inbox 2)
```bash
./venv/bin/python3 setup_gmail_auth.py \
  --inbox 2 \
  --email your-work-email@yourcompany.com
```

**What happens:**
- Browser opens
- Sign in to your Workspace account
- Grant permissions
- See "Authentication successful!"

### 3.2 Test Connection
```bash
./venv/bin/python3 test_gmail_connection.py
```

**Expected output:**
```
✅ Inbox 1 (your-personal@gmail.com): Connected
   Found 847 ORBCOMM notifications

✅ Inbox 2 (work@company.com): Connected
   Found 12 ORBCOMM notifications

🎉 All inboxes authenticated successfully!
```

---

## ✅ Step 4: You're Done! (Ready to Use)

At this point you have:
- ✅ All historical emails imported and stored
- ✅ Continuous monitoring inbox authenticated
- ✅ Database with complete history + current data

---

## 🚀 What's Next?

Now we build:

### A. Sync Engine (2-3 hours development)
- Fetch new emails daily from inbox 2
- Parse and store automatically
- Link Open/Resolved pairs
- Update stats

### B. Web Dashboard (2-3 hours development)
- Visual stats overview
- Notification list with filtering
- Open issues view
- Resolution time charts
- Export to CSV

### C. Daily Scheduler (1 hour development)
- Automated daily sync
- 180-day archive
- Stats snapshots

---

## 📊 Current Database

Check what you've got:

```bash
./venv/bin/python3 -c "
from orbcomm_tracker.database import Database
db = Database()
stats = db.get_current_stats()
print(f'Total notifications: {stats[\"total_notifications\"]}')
print(f'Open: {stats[\"open_count\"]}')
print(f'Resolved: {stats[\"resolved_count\"]}')
print(f'Avg resolution: {stats[\"avg_resolution_time_minutes\"]} min')
"
```

---

## 🎯 Timeline

**Setup (You):** 20-30 minutes
- ✅ Get credentials (10 min)
- ✅ Import historical (5-10 min)
- ✅ Auth Workspace (5 min)
- ✅ Test (2 min)

**Development (Me):** 5-7 hours
- Build sync engine (2-3 hours)
- Build web dashboard (2-3 hours)
- Add scheduler (1 hour)
- Testing (1 hour)

**Total:** Can be fully working same day!

---

## 🔧 Configuration

After setup, config file at `~/.orbcomm/config.yaml`:

```yaml
gmail:
  inboxes:
    - id: 1
      email: "personal@gmail.com"
      mode: "historical"
      enabled: false                    # Disabled after import

    - id: 2
      email: "work@company.com"
      mode: "continuous"
      enabled: true                     # Active daily sync

sync:
  interval_hours: 24                    # Daily
  continuous_inbox: 2                   # Only sync inbox 2

archive:
  archive_after_days: 180
```

---

## ❓ FAQ

**Q: Do I need to authenticate inbox 1 again?**
A: No. After historical import, inbox 1 is disabled. Never synced again.

**Q: Will it auto-sync inbox 2?**
A: Yes, once we build the scheduler (coming soon). Or run manually anytime.

**Q: What if I add more historical emails later?**
A: Just run `import_historical.py --inbox 1` again. Duplicates are skipped.

**Q: Can I use the same credentials for both?**
A: Yes! Same `credentials.json` works for both inboxes.

**Q: What about the "unverified app" warning?**
A: Normal for test apps. Click "Advanced" → "Go to ORBCOMM Tracker (unsafe)". It's safe - it's your own app.

---

## 📖 Full Documentation

- **Detailed setup:** `claudedocs/GMAIL_API_SETUP.md`
- **Inbox strategy:** `claudedocs/INBOX_STRATEGY.md`
- **System design:** `claudedocs/SYSTEM_DESIGN.md`

---

## ✅ Ready to Start?

Follow steps 1-3 above, then let me know when you're done!

I'll continue building the sync engine and dashboard while you work on setup.
