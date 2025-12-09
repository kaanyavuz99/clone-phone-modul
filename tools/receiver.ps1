# Receiver Script (Runs on VDS)
param (
    [string]$LogName = "build_unknown.log"
)

$LogDir = "C:\Users\Administrator\.gemini\RemoteLogs"
# Ensure dir exists (just in case)
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# AUTO-CLEANUP: Delete previous session logs
# We remove all build_*.log files that are NOT the current session's file.
Get-ChildItem -Path $LogDir -Filter "build_*.log" | 
Where-Object { $_.Name -ne $LogName } | 
Remove-Item -Force -ErrorAction SilentlyContinue

$LogPath = Join-Path $LogDir $LogName

try {
    # .NET way to write with Shared Access (ignores active readers)
    $Stream = [System.IO.File]::Open($LogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $Writer = New-Object System.IO.StreamWriter($Stream, [System.Text.Encoding]::UTF8)
    
    # Process Stdin Stream
    $Input | ForEach-Object {
        $Writer.WriteLine($_)
        $Writer.Flush() # Ensure real-time update
    }
}
catch {
    Write-Error "Receiver Error: $_"
}
finally {
    if ($Writer) { $Writer.Close() }
    if ($Stream) { $Stream.Close() }
}
