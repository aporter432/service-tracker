# Dual Inbox Continuous Sync

## Overview

The ORBCOMM Service Tracker now supports continuous monitoring of **both inboxes** simultaneously. This is useful when live ORBCOMM notification emails are being delivered to multiple email addresses.

## Use Case

If ORBCOMM emails are still being sent to your personal Gmail (inbox 1) while you also want to monitor a company/workspace email (inbox 2), you can now sync both inboxes continuously.

## Configuration

### Prerequisites

Both inboxes must be authenticated before syncing:

```bash
# Authenticate inbox 1 (personal Gmail)
./venv/bin/python3 setup_gmail_auth.py --inbox 1 --email personal@gmail.com

# Authenticate inbox 2 (company email)
./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email work@company.com
```

## Usage

### Manual Sync - All Inboxes

Sync both inboxes at once:

```bash
./venv/bin/python3 run_sync.py --all
```

This will:
- Fetch new emails from inbox 1 (aaron.porter225@gmail.com)
- Fetch new emails from inbox 2 (company email)
- Parse and store all emails in the database
- Link notification pairs across both inboxes
- Show a summary for each inbox

### Manual Sync - Specific Inbox

Sync only one inbox:

```bash
# Sync only inbox 1
./venv/bin/python3 run_sync.py --inbox 1

# Sync only inbox 2
./venv/bin/python3 run_sync.py --inbox 2
```

### Check Status

Check the sync status of all inboxes:

```bash
./venv/bin/python3 run_sync.py --all --status
```

This shows:
- Last sync time for each inbox
- Total notifications per inbox
- Open/Resolved counts
- Average resolution times

## Automated Scheduled Sync

The `orbcomm_scheduler.py` now defaults to syncing **both inboxes**:

```bash
# Run daily sync for both inboxes (default)
./venv/bin/python3 orbcomm_scheduler.py

# Or specify specific inboxes
./venv/bin/python3 orbcomm_scheduler.py 1 2
```

### Setting Up Automated Daily Sync

To schedule the sync to run automatically every day:

```bash
# Set up daily sync at 8:00 AM
./venv/bin/python3 setup_scheduler.py --daily 08:00
```

This will configure the scheduler to fetch from **both inboxes** daily.

## How It Works

### Inbox Sources

Each notification in the database tracks its source:
- `inbox1_continuous` - From inbox 1 ongoing sync
- `inbox2_continuous` - From inbox 2 ongoing sync
- `inbox1_historical` - From historical import (if performed)

### Duplicate Detection

The system automatically detects and skips duplicate emails across both inboxes:
- Uses Gmail message_id and thread_id
- If the same ORBCOMM notification arrives in both inboxes, only one copy is stored
- The first inbox to sync the email gets priority

### Notification Pairing

The system links Open/Resolved notification pairs:
- Pairs are matched by ORBCOMM reference number (e.g., "M-003147")
- Works across inboxes (e.g., Open email in inbox 1, Resolved email in inbox 2)
- Calculates resolution times automatically

## Benefits

1. **Complete Coverage**: Never miss an ORBCOMM notification regardless of which email address receives it

2. **Automatic Deduplication**: If the same notification arrives in both inboxes, it's only stored once

3. **Unified View**: Dashboard shows all notifications from both inboxes in one place

4. **Flexible**: Can sync both inboxes together or individually as needed

## Example Workflow

```bash
# Initial setup - authenticate both inboxes
./venv/bin/python3 setup_gmail_auth.py --inbox 1 --email aaron.porter225@gmail.com
./venv/bin/python3 setup_gmail_auth.py --inbox 2 --email work@company.com

# First sync - get last 7 days from both
./venv/bin/python3 run_sync.py --all

# Check status
./venv/bin/python3 run_sync.py --all --status

# Set up automated daily sync
./venv/bin/python3 setup_scheduler.py --daily 08:00

# Manual sync anytime
./venv/bin/python3 run_sync.py --all
```

## Troubleshooting

### One Inbox Not Authenticated

If one inbox fails with "not authenticated" error:
```bash
./venv/bin/python3 setup_gmail_auth.py --inbox N --email YOUR_EMAIL
```

The sync will still succeed for the other inbox.

### Different Sync Frequencies

If you want different sync frequencies for each inbox, run them separately:
```bash
# Daily sync for inbox 1
./venv/bin/python3 run_sync.py --inbox 1

# Hourly sync for inbox 2 (if needed)
./venv/bin/python3 run_sync.py --inbox 2
```

## Migration from Single Inbox

If you were previously syncing only inbox 2:

1. **No action needed** - The scheduler now defaults to both inboxes
2. Old data is preserved with `inbox2_continuous` source
3. New syncs will fetch from both inboxes
4. Just authenticate inbox 1 if you haven't already:
   ```bash
   ./venv/bin/python3 setup_gmail_auth.py --inbox 1 --email aaron.porter225@gmail.com
   ```

## Next Steps

After setting up dual inbox sync:

1. **Monitor Logs**: Check `~/.orbcomm/logs/` for sync status
2. **View Dashboard**: See all notifications from both inboxes
3. **Verify**: Use `--status` flag to confirm both inboxes are syncing
4. **Automate**: Set up scheduled sync for hands-off operation
