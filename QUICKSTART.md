# ORBCOMM Tracker - Quick Start Guide

## ✅ Installation Complete!

All dependencies are installed in a virtual environment.

---

## 🚀 Next Steps

### Step 1: Set Up Gmail API Credentials

You need to get OAuth credentials from Google Cloud Console.

**Follow this guide:**
```bash
open claudedocs/GMAIL_API_SETUP.md
```

**Quick summary:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project "ORBCOMM Tracker"
3. Enable Gmail API
4. Configure OAuth consent screen
5. Add both Gmail addresses as test users
6. Create OAuth credentials (Desktop app)
7. Download `credentials.json`

---

### Step 2: Authenticate Your Gmail Accounts

Once you have `credentials.json`:

**Authenticate Inbox 1:**
```bash
./venv/bin/python3 setup_gmail_auth.py --inbox 1 --email your-first-email@gmail.com
```

**Authenticate Inbox 2:**
```bash
./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email your-second-email@gmail.com
```

**Test connections:**
```bash
./venv/bin/python3 test_gmail_connection.py
```

---

## 📂 Project Structure

```
Service Tracker/
├── venv/                          # Virtual environment (✅ ready)
├── claudedocs/
│   ├── SYSTEM_DESIGN.md          # Full architecture specs
│   └── GMAIL_API_SETUP.md        # Detailed Gmail setup
├── orbcomm_tracker/
│   ├── database.py               # SQLite database (✅ ready)
│   └── [more modules coming]
├── setup_gmail_auth.py           # Gmail authentication
├── test_gmail_connection.py      # Connection tester
└── requirements.txt              # Dependencies (✅ installed)
```

---

## 💡 Using the Virtual Environment

**Always use the virtual environment when running scripts:**

```bash
# DON'T use:
python3 script.py

# DO use:
./venv/bin/python3 script.py
```

**Or activate the venv (optional):**
```bash
source venv/bin/activate
# Now you can use: python3 script.py
# Deactivate with: deactivate
```

---

## 🧪 Test Database (Optional)

Test the database layer:

```bash
./venv/bin/python3 -c "
from orbcomm_tracker.database import Database
db = Database()
print('✅ Database initialized successfully!')
print('Stats:', db.get_current_stats())
"
```

---

## 🎯 What's Next?

After Gmail authentication is complete:

1. **Initial sync** - Fetch all existing ORBCOMM emails
2. **Web dashboard** - Visual interface for tracking
3. **Daily automation** - Scheduled sync every 24 hours

---

## 📋 Current Status

✅ Virtual environment set up
✅ Dependencies installed
✅ Database layer ready
✅ Authentication scripts ready

⏳ Waiting for Gmail API credentials
⏳ Gmail authentication
⏳ Sync engine (in development)
⏳ Web dashboard (in development)

---

## 🆘 Need Help?

**Review full setup:**
```bash
open claudedocs/GMAIL_API_SETUP.md
```

**Check system design:**
```bash
open claudedocs/SYSTEM_DESIGN.md
```

**Implementation progress:**
```bash
open README_GMAIL_TRACKER.md
```

---

## 🎉 Ready When You Are!

Once you complete Gmail API setup and authentication, we'll continue building the sync engine and web dashboard.

Let me know when you're ready to proceed!
