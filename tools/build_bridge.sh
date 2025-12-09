#!/bin/bash

# VDS Information
VDS_IP="45.43.154.16"
LOG_PATH="C:\\Users\\Administrator\\.gemini\\RemoteLogs\\build.log"
SSH_SOCKET="/tmp/pio_bridge_mux_%h_%p_%r"

echo "--- Hybrid Build & Monitor (High-Speed Mux Mode) ---"
echo "Target VDS: $VDS_IP"

# 1. Start SSH Master Connection (Multiplexing)
# -M: Master mode
# -S: Socket path
# -f: Go to background
# -N: Do not execute a remote command
# -n: Redirect stdin from /dev/null
echo "Establishing high-speed link..."
ssh -M -S "$SSH_SOCKET" -fnNT -o ConnectTimeout=10 Administrator@$VDS_IP

# Function to clean up the master connection on exit
cleanup() {
    echo "Closing link..."
    ssh -S "$SSH_SOCKET" -O exit Administrator@$VDS_IP 2>/dev/null
}
trap cleanup EXIT

# 2. Clear old logs using the socket
ssh -S "$SSH_SOCKET" Administrator@$VDS_IP "powershell -Command \"Set-Content -Path '$LOG_PATH' -Value ''\""

# 3. Execution & Logging Loop
# We use a simple while loop. With the persistent socket, each 'ssh' call is nearly instant.
PIO_CMD="pio"
[ -f "$HOME/.platformio/penv/bin/pio" ] && PIO_CMD="$HOME/.platformio/penv/bin/pio"

echo "Executing Build..."

(
    # Start the build and monitor
    $PIO_CMD run -t upload && \
    $PIO_CMD device monitor
) 2>&1 | while IF= read -r line; do
    # Print to Local Screen
    echo "$line"
    
    # Send to Remote via Mux Socket
    # Escaping single quotes for PowerShell: ' -> ''
    # Using 'cmd /c echo ... >> file' might be faster than powershell for simple text, but encoding is tricky.
    # Sticking to PowerShell Add-Content for safety.
    clean_line=${line//\'/\'\'}
    ssh -S "$SSH_SOCKET" Administrator@$VDS_IP "powershell -Command \"Add-Content -Path '$LOG_PATH' -Value '$clean_line'\"" &
    # We put it in background (&) to not block the build process!
done

wait # Wait for any background log senders to finish
echo "--- Process Complete ---"
