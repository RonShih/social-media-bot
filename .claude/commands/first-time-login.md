---
description: First-time deployment — guide the user through logging into the 6 social platforms once. Sessions persist in browser_profiles/<brand>/.
---

Open each platform in order. After each, wait for the user to reply `ok` before moving on.

Order:

1. Facebook — `https://www.facebook.com/`
2. Instagram — `https://www.instagram.com/`
3. Threads — `https://www.threads.net/login` (logs in via Instagram identity)
4. X — `https://x.com/login`
5. YouTube Studio — `https://studio.youtube.com/`
6. TikTok — `https://www.tiktok.com/login`

## Flow

1. `mcp__playwright__browser_navigate` to the first platform.
2. Reply: "Log into [platform] in the browser. Reply `ok` when done and I'll move to the next."
3. On `ok` → next platform.
4. After all six → `mcp__playwright__browser_close`.
5. Tell the user: sessions saved to `browser_profiles/<brand>/`, browser closed, `publish-*` is now ready.

## Why the close at the end is mandatory

Chromium allows only one process per profile directory at a time. If `first-time-login` leaves the window open, the next `publish-*` run hits a profile lock. Close = required.

## Don'ts

- Do not click any "Save password" / browser-prompt buttons for the user.
- Do not type or autofill credentials. The user logs in by hand.
- Do not skip Threads — the login is via IG, but the Threads-specific permission grant has to happen in the Threads tab.
- Do not parallelize platforms — single browser, one tab at a time.
