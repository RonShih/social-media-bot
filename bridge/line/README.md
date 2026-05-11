# LINE bridge

Connect LINE Messaging API as the entry point for Claude Code (replacing the original Telegram channels plugin).

## Architecture

```
LINE Platform ──webhook──▶ cloudflare tunnel ──▶ webhook_server.py (FastAPI :8000)
                                                       │
                                                       │ 1. Verify X-Line-Signature
                                                       │ 2. Download media → media/inbox/line/<group>/
                                                       │ 3. Write user message to L1 buffer
                                                       │ 4. Filter by group prefix
                                                       │ 5. Build prompt (inject L1 + L2 memory)
                                                       ▼
                                              spawn `claude -p` (headless)
                                                       │
                                                       │ via mcp-config-line.json
                                                       │ loads line + playwright MCP
                                                       ▼
                                          Claude → line_send / line_push back to LINE
```

## One-time Setup

### 1. Python environment

```bash
cd bridge/line
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. LINE Developer Console

1. Go to [LINE Developers Console](https://developers.line.biz/console/) and create a Provider + Messaging API channel
2. Get two values to fill in `.env`:
   - **Channel secret** (Basic settings tab) → `LINE_CHANNEL_SECRET`
   - **Channel access token (long-lived)** (Messaging API tab, click "Issue" to generate) → `LINE_CHANNEL_ACCESS_TOKEN`
3. **Use webhook**: Enable
4. **Auto-reply messages / Greeting messages**: Disable both (otherwise LINE's built-in canned responses will interfere)
5. **Allow bot to join group chats**: Enable (primarily used in groups)

### 3. cloudflare tunnel

Allows LINE to reach your local server. If `cloudflared` is installed:

```bash
# One-time login (opens browser)
cloudflared tunnel login

# Create a fixed tunnel (recommended: URL stays constant, no need to update LINE webhook repeatedly)
cloudflared tunnel create sma-line
cloudflared tunnel route dns sma-line line.<your-domain>

# Add to ~/.cloudflared/config.yml:
#   tunnel: <tunnel-uuid>
#   credentials-file: ~/.cloudflared/<tunnel-uuid>.json
#   ingress:
#     - hostname: line.<your-domain>
#       service: http://127.0.0.1:8000
#     - service: http_status:404

cloudflared tunnel run sma-line
```

If just testing / no custom domain, use quick tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
# Prints an https://xxx.trycloudflare.com URL, changes on each restart
```

**No need to manually set webhook URL in LINE Console** — use `bind_webhook.py` in one command (see step 3 of "Start" below).

### 4. .env

```bash
cp .env.example .env
# Edit .env, fill in LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN
# CLAUDE_BIN should be an absolute path (output of `which claude`) — PATH may not resolve under launchd environment
```

## Start

Three processes / actions:

```bash
# Terminal 1: tunnel
cloudflared tunnel run sma-line          # named tunnel
# or
ssh -R 80:localhost:8000 nokey@localhost.run    # zero-config quick option

# Terminal 2: webhook server
cd <repo>
bridge/line/.venv/bin/python bridge/line/webhook_server.py

# Terminal 3 (one-time, re-run whenever tunnel URL changes): bind webhook to LINE
bridge/line/.venv/bin/python bridge/line/bind_webhook.py https://<tunnel-url>
# or type in Claude chat: /bind-line-webhook https://<tunnel-url>
```

`bind_webhook.py` does three things:
1. PUT to LINE to set webhook URL (auto-appends `/webhook` suffix)
2. POST to trigger a LINE test request (verify 200)
3. GET to confirm active=true

When you see `✅ PUT 200` + `✅ test 200 — webhook is live`, you're connected.
Add bot as a friend / invite to a group, then send a message to test.

> With a named tunnel, URL stays fixed — once configured you don't need to bind again.
> With quick tunnel / localhost.run, URL changes on each restart — re-run `bind_webhook.py`.

## Group trigger rules

- **1:1 chat**: bot always responds
- **Group / multi-person chat**: only responds if message starts with any `LINE_GROUP_PREFIXES` value (default `@editor` / `/sma`), otherwise silently ignored (but L1 buffer still written — visible next time bot is mentioned)

Examples:
- ✅ `@editor post to IG, caption: new coffee product today`
- ✅ `/sma what did we post on IG last week?`
- ❌ `nice weather today` → no reply but L1 records it

## Memory layers

| Layer | Path | Written by | Read by |
|---|---|---|---|
| L1 conversation buffer | `data/line/conversations/<group_id>.jsonl` | webhook auto-append | injected into prompt (recent N messages) on each spawn |
| L2 structured preferences | `data/line/memory/<group_id>.md` | Claude via Edit | cat'd into prompt on each spawn |
| L3 content history | `data/posts.db` (SQLite) | sync after publish-now | Claude queries via MCP tool `recall_posts` (Phase 2) |
| L4 weekly/monthly digest | `data/line/digests/*.md` | cron on Sunday / month start | digest written into L2 (Phase 3) |

Phase 1 only implements L1 + L2 read. L2 writes are handled by Claude via the Edit tool; CLAUDE.md tells it when to write.

## Acceptance criteria

- [ ] `curl http://127.0.0.1:8000/healthz` returns `{"ok": true, "ts": ...}`
- [ ] LINE Developers Console Verify button returns 200
- [ ] Sending "hi" in 1:1 gets a bot reply
- [ ] `@editor hi` in a group gets a reply; plain `hi` doesn't reply but `data/line/conversations/<group>.jsonl` has an entry
- [ ] Send image + `@editor can you see this?` in group → image lands in `media/inbox/line/<group>/`, bot reply mentions the image

## Troubleshooting

| Symptom | Fix |
|---|---|
| LINE Verify returns 403 | `LINE_CHANNEL_SECRET` is wrong, re-copy it |
| Auto-reply "Hi! We've received your message" | "Auto-reply messages" in LINE Console is not disabled |
| webhook received but bot doesn't reply | Check webhook_server stderr — did `claude -p` spawn successfully? Is `CLAUDE_BIN` correct? |
| reply_token expired | Task ran >30s with no fallback push — check `line_mcp_server.py` log |
| Push quota exhausted | Free plan allows 200 messages/month; don't send progress updates too frequently; task should only send "processing" + "done" |

## Out of scope

- Not connecting LINE Notify (deprecated)
- Not implementing LINE LIFF / Rich menu
- Not storing LINE user personal data (`data/` only stores LINE id and message text, never exported)
