#!/bin/bash

# ORBCOMM Email Parser for macOS
# Make this executable: chmod +x run_parser.sh

echo "============================================"
echo "  ORBCOMM Email Parser - macOS Version"
echo "============================================"
echo ""
echo "Instructions:"
echo "1. Copy email content from Mail/Outlook/Gmail"
echo "2. Paste when prompted"
echo "3. Type END and press Enter when done"
echo "4. Data will be saved and copied to clipboard"
echo ""
echo "Press Enter to start..."
read

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install it first."
    exit 1
fi

# Run the parser
python3 orbcomm_processor.py

echo ""
echo "============================================"
echo "Process complete!"
echo ""
echo "The CSV has been created. You can:"
echo "1. Open orbcomm_notifications.csv"
echo "2. Import to Numbers or Excel"
echo "3. Copy/paste into your tracking sheet"
echo ""
echo "Press Enter to exit..."
read
