# Development Handoff Notes

**Last Updated:** 2025-12-09
**Project:** Hybrid Dev Environment (ZorinOS Local <-> Windows VDS Remote)
**Repo:** https://github.com/kaanyavuz99/clone-phone-modul.git

## 🌍 Infrastructure Status (COMPLETED & VERIFIED)
We have successfully established a Hybrid Development Environment:
1.  **Local (ZorinOS):** Writes code, runs `pio run` (via `tools/build_bridge.sh`), uses local USB ports.
2.  **Remote (Windows VDS):** 
    - IP: `45.43.154.16`
    - User: `Administrator`
    - Path: `C:\Users\Administrator\.gemini\antigravity\scratch\HibridProje`
3.  **Log System:** 
    - **Unique Log Files:** `tools/build_bridge.sh` generates a unique `build_TIMESTAMP.log` for every session.
    - **Transport:** Uses SSH Pipe with `tee` for local mirroring + Remote `receiver.ps1` script (avoids shell escaping & file locking).
    - **Verification:** We proved we can catch syntax errors (e.g., "pintln") and receive "Heartbeat" logs in real-time.

## 🚧 Current Task: Modem Debugging
**Goal:** Establish interaction with LILYGO T-SIM7600E Modem.
- **Problem:** Initial test sent "AT" but got no response.
- **Next Step:** Write a "Passthrough" (Serial Bridge) firmware to allow manual AT command entry via terminal.

## 🛠️ Key Files
- `tools/build_bridge.sh`: The brain. Run this locally (via VS Code Task `Ctrl+Shift+B`) to build and monitor.
- `tools/receiver.ps1`: runs on VDS, handles log writing.
- `src/main.cpp`: The firmware.

## 🔄 What if VDS Reboots?
- **Settings are Permanent:** SSH keys, Firewall rules, and Git repos **WILL** survive a reboot. You do NOT need to redo them.
- **IP Address:** If your VDS has a dynamic IP, it might change after a restart.
    - **Fix:** Just update `VDS_IP="..."` in `tools/build_bridge.sh`.
    - Everything else will continue working automatically.

## 🚀 How to Resume
1.  **Open this folder.**
2.  **Read `task.md`** (it has the detailed checklist).
3.  **Start coding** `src/main.cpp` for the Serial Passthrough.
