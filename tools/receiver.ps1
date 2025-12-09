# Receiver Script (Runs on VDS)
# Reads stream from SSH Stdin and writes to log file
# This avoids complex quoting/escaping issues in the SSH command itself.

$LogPath = "C:\Users\Administrator\.gemini\RemoteLogs\build.log"

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
