# Operating Rules

Cross-platform, cross-brand enforced discipline. Every skill / command / main session must read this before handling a user request.

> Brand-specific preferences live in `config/brands/<active>.yaml`. Platform-specific UI quirks live in the matching `.claude/skills/<skill>/SKILL.md`. This file holds rules that apply to every brand on every platform.

---

## 1. Telegram channel messages always go through `reply`

When a message has a `<channel source="plugin:telegram:telegram" ...>` tag:

- Substantive responses go through `mcp__plugin_telegram_telegram__reply`. Main-session text output never reaches the user. Telegram MCP itself states: "The sender reads Telegram, not this session."
- Main-session text is fine for internal notes ("replied to TG, waiting on user"). The actual answer must be inside a `reply` call.
- Exception: terminal slash-command stdout (the `<command-name>` prefix) — that is the user typing in the terminal. Replying in the main session is correct there.

## 2. Acknowledge first

Any inbound TG message → first action is `mcp__plugin_telegram_telegram__react` with an emoji (👀 or 🔥). No exceptions, regardless of estimated response time, regardless of whether it's a Q&A or an action request.

Why: react is the lightest possible signal, does not push, and tells the user "got it, working on it" before the substantive reply lands.

Flow:

1. React first (every message, every time).
2. If task estimate exceeds 30 seconds → also `reply` "processing... estimated X minutes ...".
3. Subsequent long-progress updates use `edit_message` (edits do not push, so they don't ping the user repeatedly). When the task completes, send a fresh `reply` so the user's device pings.

> Sole exception: user sent multiple messages in quick succession and you intend to combine the response. React only the latest. Otherwise, react every message.

## 3. TG reply format: plain text, short, no markdown

Telegram's default mode does not render markdown. Tables, `#` headers, `**bold**`, `*italic*`, `` `code` ``, nested bullets — all of these show up as raw characters and look like garbage to the user.

### Required

- No markdown tables. Convert to "label: value" lines:
  - Bad: `| platform | status |` table.
  - Good: `IG: ✅ ok https://...` one line per platform.
- No `#` / `##` headers. Use a blank line + leading emoji or full-width 【】 to separate sections.
- No `**bold**`, `*italic*`, `` `code` `` wrappers. To emphasize: leading emoji (⚠️ ✅ ❌ 📌) or a half-/full-width line break.
- Paste URLs raw. No `[text](url)` markdown links.

### Short

- Default to one-line conclusion + 1-3 bullet details. No preamble, no restating the user's question.
- A reply ≤ 5 sentences is almost always enough. Beyond that, split into multiple messages or wait for "expand".
- Even for diagnostic / explanation questions: give "answer + one why" and stop. The user will ask for more if they want it.

### Emoji usage

- React (👀 🔥 👍) = "got it, started" — no text needed.
- Reply leading emoji = message-type tag (✅ success, ❌ failure, ⚠️ warn, 📸 screenshot, 📝 record, 🔗 url). One only; do not stack.

### markdownv2 mode

`mcp__plugin_telegram_telegram__reply` exposes a `format: "markdownv2"` option. Default is off — turning it on requires escaping many special characters (`.`, `-`, `!`, `_` ...). One miss and the whole message fails to send. Stay in plain-text mode unless a reply genuinely needs bold or links.

## 4. Two-stage permission gate (loose mode)

`/draft-post` and `/weekly-plan` produce previews only. Never auto-publish from a TG / Line / channel-bot session.

Flow:

1. Subagents draft → strategy preview composed (caption + hashtags + chosen platforms + media filename, plain text, no markdown).
2. `reply` the preview → write an entry to `data/pending-confirmations.json` with `expires_at = now + 5min`.
3. Next inbound message: if it matches `ok|go|yes|publish|publish now|/publish-now ...` AND exactly one un-expired entry exists → confirm and run `/publish-now`. If 2+ entries are pending → require explicit `/publish-now draft:<id>`. Otherwise echo the preview again and ask.
4. Expired → drop the entry, ask the user to re-issue `/draft-post`.

`pending-confirmations.json` shape:

```json
{
  "<draft_id>": {
    "preview_sent_at": "<ISO>",
    "platforms": ["facebook", "instagram"],
    "expires_at": "<ISO + 5min>",
    "channel": "telegram | line | cli"
  }
}
```

## 5. Process noise vs end-state truth

Most important discipline in this project. Violation → chatty UX (reporting every minor hiccup) or trust collapse (faking success).

### Process noise (mid-flow dialog / element drift / transient error / slow load) → solve silently, do not surface

- No TG `reply` / `edit_message` to "report mid-flow status".
- Unexpected dialog: judge by content.
  - Unrelated to publishing (ad upsell, onboarding nag, cookie consent, password-leak warning) → close / Escape / "Not now" / "No thanks".
  - Affects publishing (paywall, account-verify, 2FA, "add WhatsApp button") → stop and return a structured end-state error.
- Accessible-name / element-position drift → snapshot, find by role / nearby label, fall back to keyboard.
- Transient error / slow load **inside a single MCP tool call** (re-click a slow button, wait for nav) → wait + retry, ~3 attempts per call site. This is cheap — no LLM tokens spent.
- **LLM-level retry is NOT a transient-error response.** A `tool_result` returning `is_error: true`, a subagent returning `{"error": ...}`, or an MCP server reporting failure is an **end-state truth** (next section), not noise. Surface it; do not respawn the subagent, do not "try a different approach", do not silently substitute another platform. Every such retry burns tokens.

### End-state truth (anything that changes the user's world) → return structured, never fabricate

- Failure: `{"error": "<reason>", "step_failed": "<step>"}`
- URL extraction failed: `{"post_url": null, "error": "url_extraction_failed", "note": "post may have published, please verify manually"}` — do not invent a URL.
- Logged out / cookie expired: `{"error": "login expired, run /first-time-login"}`
- Profile lock conflict: `{"error": "profile lock conflict, run /unlock-browser..."}`
- Asset missing: `{"error": "asset not found: <path>"}`

### Ambiguity / 疑問 → ask, do not guess

Default disposition when something is unclear is **stop and ask**, not "pick the safest guess" or "run all reasonable options". This is the LLM-cost analogue of the `is_error` rule above: token cost of one clarifying message is far below the cost of running the wrong flow end-to-end (a wrong `/weekly-plan` is ~30 min of subagent burn).

Stop and surface a question (channel-appropriate: TG `reply`, LINE `line_send`, CLI main text) when:

- The user's instruction does not name the platform(s) / asset / target post / week.
- A required field is missing from brand YAML or plan.json (do not silently infer a default).
- Two valid interpretations of the command exist and the L1 buffer / L2 memory does not disambiguate.
- A subagent returned sparse data and proceeding would require fabricating values to fit the schema.
- You are about to make up any value to satisfy a schema.

The signal to ask: "I am about to (a) make up a value, (b) pick one of N options without a stated reason, or (c) start a non-trivial operation based on inference." Stop, surface, wait.

This does **not** override §6 — being asked to "post to all platforms" is not ambiguous and §6 still forbids skipping platforms because you predict failure. §5-ambiguity is about *what the user wants*; §6 is about *whether to attempt assigned work*.

### Hard rules — never crossable, even under "do whatever it takes"

- Never fabricate a `post_url`.
- Never click buttons of unclear meaning to push past a dialog (FB "add WhatsApp button", paid features, follow-requests, subscriptions).
- Never `pkill chrome`, `kill -9`, or delete `SingletonLock` to break a profile lock.
- Never auto-fill a password.
- Never silently respawn a subagent that returned an error — surface and stop.
- Never make up a value to fill a schema — ask the user instead.

## 6. Do not predict platform behavior

- Do not skip / reorder / rewrite strategy because "X platform usually fails / hates automation".
- Being called means the caller already decided this should run. Run all steps; only return `error` on a real failure.
- §5 covers what to do *during* a failure. §6 says do not pre-emptively avoid work the caller assigned. The two are complementary.

## 7. File-system restraint

- Do not `browser_take_screenshot` to disk (except on error, which the action-log layer handles).
- `browser_snapshot` (reads page structure, no file written) — use freely.
- Do not write per-run logs to `logs/` (action log is the only run-level log; see CLAUDE.md).
- Do not touch Google Drive / Sheets / Docs / Apps Script. All data is local.

## 8. Credentials / login

- No hardcoded credentials or tokens in code, markdown, or skills.
- All login persistence goes through Playwright's per-brand profile (`browser_profiles/<brand>/`).
- Session expired → return error pointing at `/first-time-login`. Do not attempt auto-login.

## 9. Browser lifecycle

- Every `publish-*` / `delete-*` / `first-time-login` / main-session Playwright run ends with `mcp__playwright__browser_close`.
- Not closing → next run will hit a profile lock. `browser_close` is always safe (no-op if nothing is open).
- Forbidden: `pkill chrome`, `kill -9 <pid>`, deleting `SingletonLock`.
- Profile lock error → `{"error": "profile lock conflict, run /unlock-browser or close the existing Chromium window"}`.

## 10. Action log

Every `mcp__playwright__browser_*` call during `/publish-now`, `/publish-from-plan`, `/test-roundtrip`, and the metrics-scrape and competitor-scrape steps of `/weekly-plan` is wrapped by the orchestrator and appended to `data/action-logs/<run-id>.jsonl`. Skills do not write to the action log themselves.

Schema: see `docs/ACTION_LOG.md`.

## 11. Playwright tool split

- **Writes** (publish, delete, login) → Playwright **MCP**. Action log wraps every `mcp__playwright__browser_*` call.
- **Bulk read scraping** (own-account top posts) → Node script under `scripts/scrape-*.mjs`. Independent log under `data/scrape-logs/<run-id>-<platform>.jsonl`.
- **Competitor read — public pages** → `fetch-reference` (WebFetch / WebSearch) inside a subagent. Default path for FB pages, X public profiles, YouTube channels.
- **Competitor read — login-walled platforms (IG / TikTok / Threads)** → main-session Playwright **MCP**, read-only. Constraints:
  - ≤ 3 posts per competitor URL per run (small footprint, recency-first).
  - Read-only: navigation + `og:description` extraction only. NEVER `like` / `comment` / `share` / open stories / follow.
  - Sequential in main session (subagents cannot reach MCP browser session).
  - `browser_close` on completion (per §9). Action-logged (per §10).
  - Why MCP works here: `og:description` meta tag is server-rendered for OG-protocol crawlers; surfaces likes / comments / posted_at / full caption without depending on cookies.
- MCP and the Node script **must not share** `browser_profiles/<brand>/` concurrently. Orchestrator serializes: MCP step ends with `browser_close` before any script step begins.
- Profile lock conflict → `{ "error": "profile lock conflict, run /unlock-browser..." }` per §9.

---

## Maintenance

New cross-platform rules go here. Brand-specific preferences → `config/brands/<slug>.yaml`. Platform-specific quirks → the corresponding SKILL.md's "quirks" section.
