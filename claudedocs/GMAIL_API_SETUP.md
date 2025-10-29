# Gmail API Setup Guide - Dual Inbox Configuration

## Overview

This guide walks you through setting up Gmail API access for **two separate Gmail accounts** to fetch ORBCOMM notifications.

---

## Prerequisites

- Two Gmail accounts with ORBCOMM notifications
- Google account with access to Google Cloud Console
- Python 3.9+ installed on your Mac

---

## Step 1: Enable Gmail API in Google Cloud Console

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Project name: `ORBCOMM Tracker`
4. Click **"Create"**

### 1.2 Enable Gmail API

1. In the project, go to **APIs & Services** → **Library**
2. Search for **"Gmail API"**
3. Click on it and press **"Enable"**

### 1.3 Configure OAuth Consent Screen

**IMPORTANT: Choose the right option for your setup**

#### Option A: External (For Personal Gmail + Workspace)
Choose **"External"** - works for any Gmail account

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **"External"**
3. Fill in required fields:
   - **App name**: `ORBCOMM Service Tracker`
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **"Save and Continue"**

5. **Scopes**: Click **"Add or Remove Scopes"**
   - Search for: `https://www.googleapis.com/auth/gmail.readonly`
   - Check the box next to it
   - Click **"Update"** → **"Save and Continue"**

6. **Test users**: Add both email addresses
   - Click **"Add Users"**
   - Enter personal Gmail address
   - Click **"Add Users"** again
   - Enter Google Workspace address (work-email@company.com)
   - Click **"Save and Continue"**

7. Click **"Back to Dashboard"**

**Note:** You'll see "unverified app" warnings during authentication. This is normal for test apps. Click "Advanced" → "Go to ORBCOMM Tracker (unsafe)" - it's safe, it's your own app.

#### Option B: Internal (For Google Workspace Admins Only)
If you're a Workspace admin and both accounts are in your organization:

1. Choose **"Internal"**
2. Fill in app details
3. Add Gmail readonly scope
4. No test users needed - works for whole organization
5. No "unverified" warnings

### 1.4 Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `ORBCOMM Tracker Desktop`
5. Click **"Create"**
6. Click **"Download JSON"** (save as `credentials.json`)

---

## Step 2: Prepare Your Mac Environment

### 2.1 Create Project Directory Structure

```bash
# Navigate to your project
cd ~/Projects/Service\ Tracker

# Create config directory
mkdir -p ~/.orbcomm/inbox1
mkdir -p ~/.orbcomm/inbox2

# Move credentials.json to inbox1 (we'll copy for inbox2 later)
mv ~/Downloads/credentials.json ~/.orbcomm/inbox1/
cp ~/.orbcomm/inbox1/credentials.json ~/.orbcomm/inbox2/
```

### 2.2 Install Required Python Packages

```bash
# Install Gmail API and dependencies
pip3 install --upgrade \
    google-auth \
    google-auth-oauthlib \
    google-auth-httplib2 \
    google-api-python-client \
    flask \
    flask-cors
```

---

## Step 3: Authenticate Both Inboxes

We'll create a simple authentication script that handles both accounts.

### 3.1 Run Authentication for Inbox 1

```bash
python3 setup_gmail_auth.py --inbox 1 --email your-first-email@gmail.com
```

**What happens:**
1. Browser window opens
2. Sign in to **first Gmail account**
3. Grant permissions (click "Continue")
4. See "Authentication successful!" message
5. Token saved to `~/.orbcomm/inbox1/token.json`

### 3.2 Run Authentication for Inbox 2

```bash
python3 setup_gmail_auth.py --inbox 2 --email your-second-email@gmail.com
```

**What happens:**
1. Browser window opens again
2. Sign in to **second Gmail account**
3. Grant permissions
4. Token saved to `~/.orbcomm/inbox2/token.json`

---

## Step 4: Verify Authentication

```bash
python3 test_gmail_connection.py
```

**Expected output:**
```
✅ Inbox 1 (your-first-email@gmail.com): Connected
   - Found 45 ORBCOMM notifications
   - Latest: 2025-10-28

✅ Inbox 2 (your-second-email@gmail.com): Connected
   - Found 32 ORBCOMM notifications
   - Latest: 2025-10-29

🎉 Both inboxes authenticated successfully!
```

---

## Directory Structure After Setup

```
~/.orbcomm/
├── config.yaml                # Main configuration (created by system)
├── tracker.db                 # SQLite database (auto-created)
├── tracker.log                # Application logs
├── inbox1/
│   ├── credentials.json       # OAuth credentials
│   └── token.json            # Auth token (auto-generated)
└── inbox2/
    ├── credentials.json       # OAuth credentials (same as inbox1)
    └── token.json            # Auth token (auto-generated)
```

---

## Configuration File

The system will create `~/.orbcomm/config.yaml` with this structure:

```yaml
gmail:
  inboxes:
    - name: "Inbox 1"
      email: "your-first-email@gmail.com"
      credentials_file: "~/.orbcomm/inbox1/credentials.json"
      token_file: "~/.orbcomm/inbox1/token.json"
      enabled: true

    - name: "Inbox 2"
      email: "your-second-email@gmail.com"
      credentials_file: "~/.orbcomm/inbox2/credentials.json"
      token_file: "~/.orbcomm/inbox2/token.json"
      enabled: true

  search_query: 'subject:"ORBCOMM Service Notification:"'
  max_emails_per_sync: 100

sync:
  interval_hours: 24          # Daily sync
  auto_start: false
  retry_attempts: 3

database:
  path: "~/.orbcomm/tracker.db"
  backup_enabled: true
  backup_interval_days: 7

archive:
  enabled: true
  archive_after_days: 180     # Archive after 180 days
  delete_archived: false      # Keep archived data

dashboard:
  host: "127.0.0.1"
  port: 8080
  auto_open_browser: true

logging:
  level: "INFO"
  file: "~/.orbcomm/tracker.log"
```

---

## Troubleshooting

### Issue: "Access blocked: This app isn't verified"

**Solution:**
1. Click **"Advanced"** on the warning screen
2. Click **"Go to ORBCOMM Tracker (unsafe)"**
3. This is safe - it's your own app in test mode

### Issue: "invalid_grant" error

**Solution:**
- Token expired or revoked
- Delete `token.json` and re-authenticate:
  ```bash
  rm ~/.orbcomm/inbox1/token.json
  python3 setup_gmail_auth.py --inbox 1 --email your-email@gmail.com
  ```

### Issue: "Access Not Configured"

**Solution:**
- Gmail API not enabled in Google Cloud Console
- Go back to Step 1.2 and enable Gmail API

### Issue: Second inbox authentication fails

**Solution:**
- Make sure second email was added as "Test User" in OAuth consent screen
- Go to Cloud Console → OAuth consent screen → Test users → Add user

---

## Security Notes

1. **credentials.json**: Contains OAuth client ID/secret (not sensitive alone)
2. **token.json**: Contains refresh token (keep secure, never commit to git)
3. **Permissions**: Gmail API has read-only access (`gmail.readonly` scope)
4. **Token Refresh**: Tokens auto-refresh, no re-authentication needed
5. **Revocation**: Revoke access anytime at https://myaccount.google.com/permissions

---

## Next Steps

After completing this setup:

1. ✅ Gmail API configured
2. ✅ Both inboxes authenticated
3. ✅ Ready to run initial sync

**Run first sync:**
```bash
python3 orbcomm_sync.py --initial-sync
```

**Start web dashboard:**
```bash
python3 orbcomm_dashboard.py
```

Dashboard will open at: http://localhost:8080

---

## FAQ

**Q: Do I need to re-authenticate often?**
A: No. Tokens auto-refresh and last indefinitely unless revoked.

**Q: Can I add more inboxes later?**
A: Yes. Run auth script with `--inbox 3` and update config.yaml.

**Q: What data does the app access?**
A: Only reads emails matching "ORBCOMM Service Notification:" - nothing else.

**Q: Can I run this on multiple computers?**
A: Yes, but you'll need to authenticate each computer separately.

**Q: What if I change my Gmail password?**
A: OAuth tokens remain valid after password changes.

---

## Support

If you encounter issues:
1. Check logs: `tail -f ~/.orbcomm/tracker.log`
2. Test connection: `python3 test_gmail_connection.py`
3. Re-authenticate: Delete token.json and run auth script again
