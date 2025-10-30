# ORBCOMM Email Parser - macOS (M4) Setup Guide

## 🚀 Quick Start for Mac Users

### Three Ways to Parse ORBCOMM Emails:

1. **🖥️ Native Mac GUI App** (Recommended for Mac)
2. **🌐 Web Browser Tool** (Universal)
3. **⌨️ Terminal/IDE** (For developers)

---

## Option 1: Native Mac GUI App (BEST FOR MAC)

### First Time Setup:

```bash
# Make sure Python 3 is installed (comes with macOS)
python3 --version

# Install tkinter if needed (usually pre-installed)
brew install python-tk  # Only if you have Homebrew

# Make the app executable
chmod +x orbcomm_mac_gui.py
```

### Running the App:

```bash
# From Terminal:
python3 orbcomm_mac_gui.py

# Or double-click the file if you've set Python as default
```

### GUI Features:
- **Native Mac menu bar** with keyboard shortcuts
- **Drag & drop** email files
- **Direct export** to Numbers app
- **VS Code integration**
- **Clipboard support** (⌘V to paste, ⌘C to copy)

---

## Option 2: Web Parser (Universal)

Just open `orbcomm_web_parser.html` in Safari/Chrome:
- Double-click the HTML file
- Paste email → Parse → Copy to Excel/Numbers

---

## Option 3: Terminal/IDE Integration

### VS Code Setup:

1. **Open integrated terminal** (⌃`)
2. **Run the interactive script**:
```bash
python3 orbcomm_processor.py
```

### PyCharm Setup:

1. **Add as Run Configuration**:
   - Script path: `orbcomm_processor.py`
   - Working directory: (your project folder)

2. **Run with** ⌃R (Control-R)

### Quick Terminal Commands:

```bash
# Interactive mode
python3 orbcomm_processor.py

# Process single file
python3 orbcomm_processor.py email.txt

# Batch process
python3 orbcomm_processor.py *.txt

# Make shell script executable and run
chmod +x run_parser.sh
./run_parser.sh
```

---

## 🎯 Mac-Specific Workflows

### Create a Quick Action (Automator):

1. Open **Automator**
2. Choose **Quick Action**
3. Add **Run Shell Script** action
4. Paste:
```bash
cd /path/to/your/orbcomm/folder
/usr/bin/python3 orbcomm_mac_gui.py
```
5. Save as "Parse ORBCOMM Email"
6. Now available in right-click menu!

### Alfred Workflow (if you have Alfred):

Create a keyword trigger:
```bash
# Keyword: orbcomm
# Script:
cd ~/Documents/orbcomm && python3 orbcomm_mac_gui.py
```

### Raycast Script (if you have Raycast):

```bash
#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Parse ORBCOMM Email
# @raycast.mode silent

cd ~/Documents/orbcomm
python3 orbcomm_mac_gui.py
```

---

## 📊 Excel/Numbers Integration

### For Excel on Mac:
1. Parse emails with any method above
2. Click "Copy for Excel"
3. Open Excel
4. Select cell A1 in your tracking sheet
5. Paste (⌘V)

### For Numbers:
1. Parse emails
2. Click "Open in Numbers" button (GUI app)
3. Numbers opens automatically with your data
4. Copy/paste to your master sheet

### For Google Sheets:
1. Parse emails
2. Export as CSV
3. Import into Google Sheets (File → Import)

---

## 🛠️ IDE Development Setup

### Project Structure:
```
orbcomm_project/
├── orbcomm_mac_gui.py      # Mac native GUI
├── orbcomm_processor.py    # Terminal interactive
├── orbcomm_email_parser.py # Core parsing library
├── orbcomm_web_parser.html # Web interface
├── run_parser.sh           # Shell script
├── emails/                 # Store .txt or .eml files here
├── exports/                # CSV exports go here
└── ORBCOMM_Tracking_Template.xlsx
```

### VS Code Tasks (tasks.json):
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run ORBCOMM Parser",
            "type": "shell",
            "command": "python3",
            "args": ["orbcomm_processor.py"],
            "group": {
                "kind": "build",
                "isDefault": true
            }
        },
        {
            "label": "Launch GUI",
            "type": "shell",
            "command": "python3",
            "args": ["orbcomm_mac_gui.py"]
        }
    ]
}
```

### VS Code Launch Configuration (launch.json):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "ORBCOMM Parser",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/orbcomm_processor.py",
            "console": "integratedTerminal"
        },
        {
            "name": "ORBCOMM GUI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/orbcomm_mac_gui.py"
        }
    ]
}
```

---

## 🔥 Pro Tips for Mac Users

### Email App Integration:

**Mail.app**:
- Select email → File → Save As → Save as .txt
- Drag into parser GUI

**Outlook for Mac**:
- Select email → File → Save As → Text Only
- Process with parser

**Gmail (Web)**:
- Print → Save as PDF → Copy text
- Or use "Show Original" → Copy

### Keyboard Shortcuts (GUI App):
- **⌘V** - Paste email content
- **⌘N** - Clear all
- **⌘S** - Save as CSV
- **⌘E** - Export to Excel format
- **⌘O** - Open email file
- **⌘Q** - Quit

### Terminal Aliases (.zshrc):
```bash
# Add to ~/.zshrc
alias orbcomm='cd ~/Documents/orbcomm && python3 orbcomm_processor.py'
alias orbcomm-gui='cd ~/Documents/orbcomm && python3 orbcomm_mac_gui.py'
```

### Batch Processing:
```bash
# Process all .txt files in a directory
find ~/Downloads -name "ORBCOMM*.txt" -exec python3 orbcomm_processor.py {} \;
```

---

## 📱 iOS Shortcut (for iPhone/iPad)

If you save emails on iOS and sync via iCloud:
1. Save email as text in Files app
2. Share to Mac via AirDrop or iCloud
3. Process with parser

---

## ⚡ Performance on M4 Mac

The scripts are optimized for Apple Silicon:
- Native Python 3 (ARM64)
- Minimal dependencies
- Fast CSV processing
- Instant clipboard operations

---

## 🆘 Troubleshooting

### "Python not found":
```bash
# Install via Xcode Command Line Tools
xcode-select --install
```

### "tkinter not found":
```bash
# If you have Homebrew:
brew install python-tk

# Or use the web version instead
open orbcomm_web_parser.html
```

### Permission denied:
```bash
chmod +x *.py *.sh
```

### VS Code can't find python:
1. Open Command Palette (⌘⇧P)
2. Type "Python: Select Interpreter"
3. Choose `/usr/bin/python3`

---

## Need Help?

- The **GUI app** is the most Mac-friendly option
- The **web parser** works everywhere
- For automation, use the **terminal scripts**
- For development, integrate with your **IDE**

Remember: All tools produce the same output - choose based on your workflow!
