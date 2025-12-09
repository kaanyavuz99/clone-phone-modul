#!/bin/bash

# VDS Information
VDS_IP="45.43.154.16"
# Remote Path (Windows format, escaped backslashes)
LOG_PATH="C:\\Users\\Administrator\\.gemini\\RemoteLogs\\build.log"

echo "--- Hybrid Build Starting (Linux Client) ---"
echo "Target: $VDS_IP"

# Simulate Build Process
echo "Simulating build..."
sleep 1
echo "Scanning libraries..."
sleep 1
echo "BUILD SUCCESS!"

# Function to send log to VDS
send_log() {
    local line="$1"
    # Execute PowerShell command on VDS to append log
    # Removed silencers to debug connection
    ssh Administrator@$VDS_IP "powershell -Command \"Add-Content -Path '$LOG_PATH' -Value '$line'\""
}

# Example of piping output (Simplified for avoiding complexity with pipe | ssh in bash for now)
# For a real build, we would do: make | while read line; do ... done
# Here we just send a success message for verification

send_log "--- New Build from Linux Client ---"
send_log "Build completed successfully."

echo "--- Process Complete ---"
