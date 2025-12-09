#!/bin/bash

# VDS Information
VDS_IP="45.43.154.16"
# This path must match where the repo is cloned on the VDS
REMOTE_REPO_PATH="C:\\Users\\Administrator\\.gemini\\antigravity\\scratch\\HibridProje"
RECEIVER_SCRIPT="$REMOTE_REPO_PATH\\tools\\receiver.ps1"
LOG_PATH="C:\\Users\\Administrator\\.gemini\\RemoteLogs\\build.log"

echo "--- Hybrid Build & Monitor (Stream Pipe Mode) ---"
echo "Target VDS: $VDS_IP"

# 1. Locate PlatformIO Core
PIO_CMD="pio"
[ -f "$HOME/.platformio/penv/bin/pio" ] && PIO_CMD="$HOME/.platformio/penv/bin/pio"

# 2. Generate Unique Session ID (Avoids Windows File Locking)
SESSION_ID=$(date +%s)
LOG_FILENAME="build_${SESSION_ID}.log"
echo "Session Log File: $LOG_FILENAME"

# 3. Execution (The Simple Pipe)
echo "Starting Stream..."

# We pipe output to receiver.ps1, passing the unique filename
(
    $PIO_CMD run -t upload && \
    $PIO_CMD device monitor
) 2>&1 | ssh Administrator@$VDS_IP "powershell -ExecutionPolicy Bypass -File \"$RECEIVER_SCRIPT\" -LogName \"$LOG_FILENAME\""

echo "--- Process Complete ---"
