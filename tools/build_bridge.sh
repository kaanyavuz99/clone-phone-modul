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

# 2. Clear previous logs
ssh Administrator@$VDS_IP "powershell -Command \"Set-Content -Path '$LOG_PATH' -Value ''\""

# 3. Execution (The Simple Pipe)
echo "Starting Stream..."

# We pipe the output directly to the remote receiver script.
# The receiver script reads Stdin and writes to the log file.
(
    $PIO_CMD run -t upload && \
    $PIO_CMD device monitor
) 2>&1 | ssh Administrator@$VDS_IP "powershell -ExecutionPolicy Bypass -File \"$RECEIVER_SCRIPT\""

echo "--- Process Complete ---"
