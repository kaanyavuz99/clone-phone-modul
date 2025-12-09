#!/bin/bash

# VDS Information
VDS_IP="45.43.154.16"
LOG_PATH="C:\\Users\\Administrator\\.gemini\\RemoteLogs\\build.log"

echo "--- Hybrid Build & Monitor Starting ---"
echo "Target VDS: $VDS_IP"

# 0. Clear previous logs (New Session)
echo "Initializing new session..."
ssh Administrator@$VDS_IP "powershell -Command \"Set-Content -Path '$LOG_PATH' -Value ''\""

# 1. Locate PlatformIO Core
PIO_CMD="pio"
if ! command -v pio &> /dev/null; then
    if [ -f "$HOME/.platformio/penv/bin/pio" ]; then
        PIO_CMD="$HOME/.platformio/penv/bin/pio"
        echo "Found PIO at: $PIO_CMD"
    else
        echo "ERROR: 'pio' command not found!"
        echo "Please install PlatformIO or add it to your PATH."
        exit 1
    fi
fi

# 2. Function to send logs
send_log() {
    local line="$1"
    # Send to VDS (Escape single quotes in the content)
    clean_line=$(echo "$line" | sed "s/'/''/g")
    ssh Administrator@$VDS_IP "powershell -Command \"Add-Content -Path '$LOG_PATH' -Value '$clean_line'\""
}

# 3. Execution (Upload + Monitor)
# We execute the command and pipe the output to a loop
echo "Executing: $PIO_CMD run -t upload && $PIO_CMD device monitor"

# Using a subshell to combine streams
($PIO_CMD run -t upload && $PIO_CMD device monitor) 2>&1 | while IF= read -r line; do
    echo "$line"   # Print to Local Terminal
    send_log "$line" # Send to VDS
done
