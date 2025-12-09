#!/bin/bash

# VDS Information
VDS_IP="45.43.154.16"
# Remote Path (Windows format)
LOG_PATH="C:\\Users\\Administrator\\.gemini\\RemoteLogs\\build.log"

echo "--- Hybrid Build & Monitor Starting (Persistent Tunnel Mode) ---"
echo "Target VDS: $VDS_IP"

# 1. Locate PlatformIO Core
PIO_CMD="pio"
if ! command -v pio &> /dev/null; then
    if [ -f "$HOME/.platformio/penv/bin/pio" ]; then
        PIO_CMD="$HOME/.platformio/penv/bin/pio"
    else
        echo "ERROR: 'pio' command not found!"
        exit 1
    fi
fi

# 2. Clear previous logs
echo "Initializing new session..."
ssh -o BatchMode=yes -o ConnectTimeout=5 Administrator@$VDS_IP "powershell -Command \"Set-Content -Path '$LOG_PATH' -Value ''\""

# 3. Execution with Persistent Tunnel
# We use 'tee' and Process Substitution >(...) to stream output to SSH in real-time.
# The remote command 'cmd /c type CON >> ...' reads from Stdin and appends to file efficiently.

echo "Starting Build & Monitor..."

(
    $PIO_CMD run -t upload && \
    $PIO_CMD device monitor
) 2>&1 | tee >(ssh Administrator@$VDS_IP "cmd /c type CON >> \"$LOG_PATH\"")

echo "--- Session Ended ---"
