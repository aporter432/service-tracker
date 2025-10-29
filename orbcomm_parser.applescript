#!/usr/bin/osascript

(*
ORBCOMM Email Parser - AppleScript Version
Save this as an Application for drag-and-drop functionality
Or use with Automator for Quick Actions

Usage:
1. Save as .scpt or .app
2. Drop email text files onto it
3. Or run and paste when prompted
*)

on run
    display dialog "Paste your ORBCOMM email content:" default answer "" with icon note buttons {"Cancel", "Parse"} default button "Parse" with title "ORBCOMM Email Parser"
    
    set emailContent to text returned of result
    
    if emailContent is not "" then
        parseORBCOMMEmail(emailContent)
    end if
end run

on open droppedItems
    repeat with anItem in droppedItems
        set fileContent to read anItem
        parseORBCOMMEmail(fileContent)
    end repeat
end open

on parseORBCOMMEmail(emailText)
    -- Create a temporary file with the email content
    set tempFile to "/tmp/orbcomm_temp.txt"
    
    do shell script "echo " & quoted form of emailText & " > " & tempFile
    
    -- Run the Python parser
    set parseResult to do shell script "cd /path/to/orbcomm/folder && python3 -c '
import re
from datetime import datetime

text = open(\"" & tempFile & "\").read()

# Extract key information
reference = \"\"
platform = \"\"
event = \"\"
status = \"Open\"

if \"Reference#\" in text:
    match = re.search(r\"([A-Z]-\\d{6})\", text)
    if match:
        reference = match.group(1)

if \"Platform:\" in text:
    match = re.search(r\"Platform:\\s*([^\\n]+)\", text)
    if match:
        platform = match.group(1).strip()

if \"Event:\" in text:
    match = re.search(r\"Event:\\s*([^\\n]+)\", text)
    if match:
        event = match.group(1).strip()

if \"resolved\" in text.lower():
    status = \"Resolved\"

# Format output
output = f\"Reference: {reference}\\nPlatform: {platform}\\nEvent: {event}\\nStatus: {status}\"
print(output)
'"
    
    -- Display results
    display dialog "Parsed ORBCOMM Notification:" & return & return & parseResult buttons {"Copy to Clipboard", "OK"} default button "Copy to Clipboard" with icon note with title "Parse Results"
    
    if button returned of result is "Copy to Clipboard" then
        set the clipboard to parseResult
        display notification "Results copied to clipboard" with title "ORBCOMM Parser"
    end if
    
    -- Clean up
    do shell script "rm -f " & tempFile
end parseORBCOMMEmail
