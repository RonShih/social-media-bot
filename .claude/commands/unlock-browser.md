---
description: Clear a stuck Chromium profile lock when publish-* fails with "profile lock conflict".
---

## Flow

1. `mcp__playwright__browser_close` (always safe — no-op if nothing is open).
2. Wait 1 second.
3. Check whether any Chromium process still holds the brand profile:
   ```bash
   pgrep -af "Chromium.*browser_profiles/<active brand>"
   ```
4. If a process is found:
   - Show the PID + command line to the user.
   - Ask: "Process PID=<n> is using browser_profiles/<brand>. Did you start that one yourself?"
   - On `yes / kill it` → `kill <pid>`.
   - On `no` or unsure → stop, do not kill.
5. If no process is found but the lock file remains:
   - `ls -la browser_profiles/<brand>/SingletonLock` and show output.
   - Ask: "No process is holding the profile but the lock file exists. Remove it?"
   - On `yes` → `rm browser_profiles/<brand>/SingletonLock`.
   - On `no` → stop.

## Don'ts

- Do not kill processes or delete the lock without asking.
- Do not switch `--user-data-dir` to bypass the lock — that loses cookies.
- Do not retry more than once per session.

## Why two paths

- Process exists: might be a debugging Chromium the user opened intentionally. Killing blindly destroys their work.
- No process, lock present: a previous Chromium crashed without cleaning up. Removing the orphaned lock is safe.
