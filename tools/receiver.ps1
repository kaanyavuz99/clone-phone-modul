# Receiver Script (Runs on VDS)
# Reads stream from SSH Stdin and writes to log file
# This avoids complex quoting/escaping issues in the SSH command itself.

$LogPath = "C:\Users\Administrator\.gemini\RemoteLogs\build.log"

try {
    # $Input is the automatic variable for Stdin in PowerShell
    $Input | Out-File -FilePath $LogPath -Append -Encoding UTF8 -Force
}
catch {
    Write-Error "Receiver Error: $_"
}
