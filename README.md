# social-media-bot

Multi-brand social-media operator for Facebook, Instagram, X, Threads, YouTube, TikTok. LLM-driven via Claude Code, browser-driven via Playwright MCP. No platform APIs, no cloud, no secrets in repo. Two channel front-ends: **Telegram** (Claude Code channels plugin) and **LINE** (self-hosted webhook + LINE Messaging API bridge).

## What it does

- Drafts captions + hashtags per platform (preview only).
- Publishes image / video posts via Playwright (FB, IG, X, Threads support post + video; YouTube and TikTok are video-only).
- Generates weekly plans with research, scheduling, drafts, and an xlsx export. Tracks posted URLs and feeds last week's metrics back into next week's plan.
- Logs every Playwright `browser_*` call to JSONL for future scriptification.
- Tests in two modes: `dry-run` (stop before final Publish click) or `roundtrip` (real publish + matching `delete-*` + verify removed).

## Setup (per machine)

1. `cp .claude/settings.example.json .claude/settings.json`
   - Edit the `--user-data-dir` path to your absolute repo path + `/browser_profiles/<brand>`.
2. `echo noirs-boxes > config/active-brand` (or whichever brand slug you want active).
3. `npm install exceljs` (used by `scripts/plan-export.mjs` and `scripts/plan-import.mjs`).
4. Open Claude Code in the repo and run `/setup` if you want to edit the brand YAML interactively, or edit `config/brands/<slug>.yaml` directly.
5. Run `/first-time-login` once to log into each platform. Sessions persist in `browser_profiles/<brand>/`.

## Daily usage

Direct posting:

```
/draft-post fb,ig,x,threads --url https://news.example.com/article
# review preview
/publish-now draft:<id>
```

Plan-driven:

```
/weekly-plan                 # generate this week's plan
/publish-from-plan --day today
```

Pre-flight:

```
/test-roundtrip facebook --mode dry-run
/test-roundtrip threads --mode roundtrip   # real publish + delete + verify
```

## Layout

- `config/brands/` — brand profiles. `_example.yaml` is the schema; `<slug>.yaml` is per-brand.
- `config/active-brand` — one-line slug picking the active brand.
- `.claude/skills/` — capabilities. One skill per platform action; brand-agnostic.
- `.claude/commands/` — slash commands. Orchestrate skills.
- `bridge/line/` — LINE channel front-end (webhook server, MCP server, memory store, webhook binder). See `bridge/line/README.md`.
- `templates/CLAUDE.user.md` — copy into `~/.claude/CLAUDE.md` on the user's machine to get the bot-session UX (ack-first, plain text, two-stage gate). Telegram-oriented; LINE has its own rules in `bridge/line/RULES.md`.
- `docs/` — operating rules, weekly-plan reference, action-log schema.
- `scripts/` — Node helpers (`plan-export.mjs`, `plan-import.mjs`, `action-log-summarize.mjs`).
- `media/assets/<brand>/` — image / video library; `inbox/` for Telegram-uploaded files.
- `media/inbox/line/<group_id>/` — LINE-uploaded media (channel-keyed; the webhook server pulls attachments via the LINE content API).
- `reports/` — drafts, posts, weekly plans (per brand).
- `data/action-logs/`, `data/runs/` — JSONL action logs + run metadata.
- `data/line/conversations/`, `data/line/memory/` — LINE L1 rolling buffer + L2 structured preferences (gitignored).
- `browser_profiles/<brand>/` — Chromium persistent profile (gitignored).

## Multi-brand

- One repo, many brand profiles under `config/brands/`.
- Switch active brand by editing `config/active-brand` or exporting `BRAND=<slug>`.
- Each brand has its own `browser_profiles/<brand>/` (separate logins).
- Skills are brand-agnostic; everything brand-specific reads from the brand YAML.

## Channel front-ends

Two independent ways to talk to the bot. Pick one or run both at the same time — commands, skills, and brand YAML are all channel-agnostic.

### Telegram (Claude Code channels plugin)

No process in this repo; the official plugin runs the long-poll. Copy `templates/CLAUDE.user.md` into the operator machine's `~/.claude/CLAUDE.md`, then:

```
claude --channels plugin:telegram@claude-plugins-official
```

That template makes Claude:

- React 👀 immediately on every inbound message.
- Reply in plain text, no markdown.
- Run `/draft-post` and `/weekly-plan` as preview-only.
- Wait for "ok" / "go" / "yes" / explicit slash command before `/publish-now`.

### LINE (self-hosted webhook bridge)

`bridge/line/` ships a FastAPI webhook server, a small MCP server exposing `line_send` / `line_reply` / `line_push`, and a one-shot CLI for binding the webhook URL to your LINE Messaging API channel.

Per-message flow: webhook arrives → signature verified → media pulled into `media/inbox/line/<group_id>/` → group/prefix filter → L1 + L2 memory injected into prompt → fresh `claude -p` session spawned → Claude calls `line_send` to reply through the LINE API.

```bash
# 1. Python env
cd bridge/line
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Credentials
cp .env.example .env
# Fill in LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, CLAUDE_BIN (absolute path recommended)

# 3. Run two processes
cloudflared tunnel run sma-line                                  # Terminal 1 — public HTTPS tunnel
bridge/line/.venv/bin/python bridge/line/webhook_server.py       # Terminal 2 — webhook server

# 4. Bind the webhook URL to your LINE channel (one-off; re-run when tunnel URL changes)
/bind-line-webhook https://line.<your-domain>.com
# or directly:  bridge/line/.venv/bin/python bridge/line/bind_webhook.py https://...
```

Full setup steps and troubleshooting: [`bridge/line/README.md`](bridge/line/README.md).
LINE-specific operating rules (override the TG bits of `docs/OPERATING_RULES.md`): [`bridge/line/RULES.md`](bridge/line/RULES.md).

### Telegram vs LINE — quick comparison

| Dimension | Telegram | LINE |
|---|---|---|
| Receive mechanism | Long-poll (no public URL needed) | Webhook (HTTPS public URL required) |
| Session model | Long-lived (one Claude session sees every message) | Stateless (fresh `claude -p` per inbound message) |
| Reaction emoji | ✅ supported (used as the "got it" signal) | ❌ not supported |
| Edit message | ✅ supported (silent progress updates) | ❌ not supported |
| Attachment ingest | ✅ auto-downloaded by the plugin | ✅ pulled by webhook via content API |
| Quota | Effectively unlimited | Reply tokens free unlimited; push 200/month free tier (**default = reply only**) |
| Deployment | Bot token only | Cloudflare Tunnel / ngrok + LINE Developer Console |
| Conversation memory | In-session only (lost on restart) | L1 + L2 file-backed (`data/line/`) |
| Context bloat | Yes (mitigated by subagents) | No (stateless, memory injected per message) |

Both channels invoke the same `/draft-post`, `/publish-now`, `/weekly-plan` flow. The two-stage permission gate (`docs/OPERATING_RULES.md` §4) applies to both.

### LINE three-tier memory

LINE is stateless per message; continuity comes from files injected at the top of every prompt:

| Tier | Content | Path | Injection |
|---|---|---|---|
| L1 conversation buffer | Last N messages exchanged in this group / 1:1 | `data/line/conversations/<group_id>.jsonl` | Webhook auto-appends and prepends most-recent N to the prompt |
| L2 structured preferences | "What this customer / group prefers" — brand, voice, recurring rules | `data/line/memory/<group_id>.md` | Auto-cat into the prompt; Claude maintains it via the `Edit` tool |
| L3 post history | Past published posts (Phase 2) | `data/posts.db` (SQLite) | Lazy lookup via an MCP tool — not yet implemented |
| L4 weekly / monthly digest | Rolled-up insights (Phase 3) | `data/line/digests/*.md` | Cron-generated; insights flow back into L2 |

Phase 1 covers L1 and L2 read. L2 writes are Claude's job — `bridge/line/RULES.md` tells it when to record a long-term fact.

See `docs/HOW_TO_USE.md` for the full operator playbook.
