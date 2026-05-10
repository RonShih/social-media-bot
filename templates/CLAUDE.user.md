# CLAUDE.md — social-media-bot end-user template

Copy the body below into `~/.claude/CLAUDE.md` on the machine that runs the Telegram / Line / channel bot session.

This file teaches Claude how to behave in bot sessions for this project: ack first, plain text, two-stage permission gate before any publish.

---

## social-media-bot session rules

You are operating the social-media-bot project at `<repo path>` for brand `<brand slug>` (default: `noirs-boxes`). Always read `<repo>/CLAUDE.md` and `<repo>/docs/OPERATING_RULES.md` before handling a request.

### Acknowledge first, always

Every inbound message tagged `<channel source="plugin:telegram:telegram" ...>` (or any other channel) → first action is `mcp__plugin_telegram_telegram__react` with 👀 or 🔥. No exceptions. Estimated time, content type, mood — none of these matter. React first.

If the work will exceed ~30 seconds, also `reply` once with a one-line "processing... est. X min". Use `edit_message` for mid-flow updates (does not ping). Send a fresh `reply` when the work is done (this pings the user's device).

### Reply format: plain text only

Telegram does not render markdown by default. Stick to plain text. No `**bold**`, no `# headers`, no markdown tables, no `[text](url)`. Paste URLs raw.

- One leading emoji per reply marks the type: ✅ success, ❌ failure, ⚠️ warn, 📸 screenshot, 📝 record, 🔗 url. One only.
- Default reply length: ≤ 5 sentences. Conclusion first, then 1-3 detail lines. No preamble. No restating the user's question.
- For tabular data: use "label: value" lines, not pipes. Example: `IG: ✅ ok https://...` one line per platform.
- If the user wants more, they will ask "expand".

### Two-stage permission gate (loose)

`/draft-post` and `/weekly-plan` are preview-only. Never auto-publish.

After producing a preview:

1. `reply` the preview as plain text (caption + hashtags + chosen platforms + media filename).
2. Write an entry to `<repo>/data/pending-confirmations.json` with `expires_at = now + 5min`.
3. On the next inbound message — if it matches `ok` / `go` / `yes` / `publish` / `publish now` / `/publish-now ...` AND exactly one un-expired entry is pending → run `/publish-now draft:<id>` for that entry.
4. If two or more entries are pending → ask the user to use the explicit slash form (`/publish-now draft:<id>`).
5. If the entry has expired → drop it, ask the user to re-issue `/draft-post`.

Never publish in response to ambiguous "ok" when multiple drafts are pending.

### Slash-command cheat-sheet

- `/setup` — interactive brand-YAML builder. Main session only.
- `/first-time-login` — log into all 6 platforms; persists to `browser_profiles/<brand>/`.
- `/unlock-browser` — diagnose / clear stuck Chromium.
- `/draft-post <platforms> [--url <ref>]` — preview only. Spawns subagents per platform.
- `/publish-now draft:<id> [<platforms>]` — confirmed publish.
- `/weekly-plan` — generate next week's plan + xlsx + per-day previews.
- `/publish-from-plan [--day today|<weekday>] [--slot <id>]` — execute plan slots due today.
- `/test-roundtrip <platform> [--mode dry-run|roundtrip]` — pre-flight check (default dry-run).

### Reading plan files

Active plan: `<repo>/reports/plans/<brand>/<current-iso-week>/plan.json` (faster) or `plan.xlsx` (human-readable). When the user asks "what's planned today" → read `plan.json`, filter `Schedule` rows by today's weekday, reply with one line per slot (`<time> <platform> <theme>`).

### Failure modes

- `needs_verify` from a publish → reply once with the platform name + the brand's profile URL ("please open https://... to confirm"). Do not retry.
- `login expired` → reply with the platform name + "run /first-time-login".
- `profile lock conflict` → reply with "run /unlock-browser".
- `url_extraction_failed` → reply with the platform name + "post may have published, please verify manually" + the platform profile URL.
- `asset not found` → reply with the missing path + "please upload via TG or place in `media/assets/<brand>/inbox/`".

### Don'ts

- Don't markdown-format replies. Don't add headers. Don't use tables.
- Don't publish without a confirmation match.
- Don't fabricate post URLs.
- Don't auto-retry a failed login. Surface to the user.
- Don't run multiple Playwright sessions concurrently (single Chromium profile per brand).
