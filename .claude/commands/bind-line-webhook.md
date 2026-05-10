---
description: Bind a tunnel URL to the LINE Messaging API channel webhook and verify via LINE API
argument-hint: "[tunnel URL, optional → auto-detect ngrok]"
---

Set the LINE channel webhook URL to the specified tunnel URL (cloudflared / ngrok / localhost.run all supported), then trigger LINE to make a real verification request (expect 200).

## Steps

1. **Find URL**:
   - User provided → use as-is (auto-append `/webhook` suffix)
   - Not provided → run `python bridge/line/bind_webhook.py`, script auto-detects ngrok local API
   - Neither works → tell user "no URL provided and no tunnel found — please paste the URL printed by cloudflared / localhost.run"

2. **Execute**:
   ```bash
   bridge/line/.venv/bin/python bridge/line/bind_webhook.py "<URL>"
   ```

3. **Parse result**:
   - PUT 200 + test success → reply "✅ Bound successfully, webhook is live"
   - PUT 200 + test failed → reply "⚠️ URL was set but LINE test did not pass" + failure reason + suggestions (webhook_server not running? tunnel not connected?)
   - PUT failed → reply "❌ Setup failed" + status code (401 = wrong token, 400 = bad URL format)

## Don't

- Don't curl LINE API directly — always go through `bind_webhook.py` (reads `.env` for token, has verify flow)
- Don't guess the URL when not provided (e.g. reconstruct from cloudflared output) — if not detected, stop and ask
- Don't print the access token

## Common variants

- Check current webhook setting only: `python bridge/line/bind_webhook.py --show`
- Re-test without changing URL: `python bridge/line/bind_webhook.py <current-URL>` also runs the test
