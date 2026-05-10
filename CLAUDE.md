# social-media-bot — project memory

## Read before any work

Any session (main or subagent) handling a user request must read first:

1. `docs/OPERATING_RULES.md` — cross-platform discipline (TG reply, processing signal, noise-vs-truth, browser lifecycle, two-stage permission gate)
2. `config/brands/<active>.yaml` — the active brand profile (resolved below)
3. The relevant `.claude/skills/<skill>/SKILL.md` for the task at hand

`docs/OPERATING_RULES.md` is enforced discipline, not advice. Violating it is a bug.
Brand-specific preferences live in the brand YAML; platform-specific UI quirks live in the matching SKILL.md. Do not mix them.

## Active brand resolution

In order:
1. `BRAND` environment variable
2. `config/active-brand` (one-line slug; default file ships with `noirs-boxes`)
3. CLAUDE.md pin (this file): default brand is `noirs-boxes`

The resolved slug points at `config/brands/<slug>.yaml`. Skills read brand context from this YAML — never hardcode brand values into skills or commands.

## Identity

Multi-brand social-media operator. Brand identity (company, voice, products, social handles, content style, forbidden words) comes exclusively from the active brand YAML. The same skill set serves every brand.

If `config/brands/<active>.yaml` is missing or looks empty (no `display_name`, no `socials.*.url`) → tell the user to run `/setup`.

## File conventions

- Drafts: `reports/drafts/<brand>/<draft_id>.json` — phase 1 output of `/draft-post`. `draft_id` format: `YYYYMMDD-HHMMSS` (direct-publish suffix `-direct`).
- Posts: `reports/posts/<brand>/<draft_id>-<platform>.md` — phase 2 result of `/publish-now` (one file per platform).
- Plans: `reports/plans/<brand>/<YYYY-Www>/{plan.json, plan.xlsx, research/}` — `plan.json` is the source of truth; `plan.xlsx` is regenerated from it.
- Action logs: `data/action-logs/<run-id>.jsonl` + sibling `data/runs/<run-id>.meta.json`. Run ID format: `YYYYMMDD-HHMMSS-<rand4>`.
- Pending bot confirmations: `data/pending-confirmations.json` (5-minute TTL on each entry).
- Stats history: `data/stats-history/<brand>.json` — rolled-up post metrics for next-week feedback.
- Assets: `media/assets/<brand>/...` and `media/assets/<brand>/inbox/` for Telegram-uploaded files.
- Browser profile: `browser_profiles/<brand>/` — Playwright `--user-data-dir` is per-brand.

## Operating rules — work principles

1. Read the matching `.claude/commands/<command>.md` before executing a slash command.
2. Skills are single capabilities. When a command needs X → read `.claude/skills/X/SKILL.md` and follow its steps.
3. Skills do not call other skills. Composition is the command's job. (Exception: a command may parallelize multiple sibling skills, e.g. `/draft-post fb,ig,x` spawns 3 `draft-*` subagents.)
4. All platform interactions go through Playwright MCP. No platform APIs, no fallbacks to APIs.
5. All data is local. No Google Drive / Sheets / Docs / Apps Script.

## Subagent discipline

Channel sessions (e.g. `claude --channels plugin:telegram@...`) are long-lived; context accumulates. Pure LLM work goes in subagents to keep main-session context clean. But Playwright MCP cannot be reached from subagents (browser session does not propagate) — anything touching the browser must run in the main session.

Rules:

1. `/draft-post`, `/weekly-plan` — main session spawns one `draft-<platform>` (or `weekly-plan-draft`/`weekly-plan-research`) subagent per platform/slot, in parallel. Pure LLM, no browser.
2. `/publish-now`, `/publish-from-plan`, `/test-roundtrip` — main session runs Playwright directly, sequential per platform. `browser_close` between platforms.
3. `fetch-reference` always in a subagent.
4. Interactive commands (`/setup`, `/first-time-login`, `/unlock-browser`) main session only.
5. If the user says "do not subagent, just do it" → entire flow in the main session.

## Two-stage permission gate (loose mode)

`/draft-post` and `/weekly-plan` produce previews. Never auto-publish.

1. Bot session reacts (👀) on the inbound message immediately.
2. Drafting runs in subagents → strategy preview composed: caption + hashtags + chosen platforms + media filename, plain text, no markdown.
3. Reply preview to user → write entry to `data/pending-confirmations.json` with `expires_at = now + 5min`.
4. Next user message: if it matches `ok|go|yes|publish|publish now|/publish-now ...` AND there is exactly one un-expired pending entry → treat as confirmation for that draft. If two or more pending → require explicit `/publish-now draft:<id>`.
5. Confirmed → orchestrator runs `/publish-now`, writes action log, replies post URLs.
6. Expired → drop the entry; ask the user to re-issue `/draft-post`.

## Action log requirement

Orchestrator (the slash-command code path) wraps every `mcp__playwright__browser_*` call during `/publish-now`, `/publish-from-plan`, `/test-roundtrip`, and the metrics-scrape step of `/weekly-plan`, and appends one JSON object per call to `data/action-logs/<run-id>.jsonl`. Skill files do not write logs themselves — keep skills declarative.

## Testing rules

- `/test-roundtrip` defaults to `--mode dry-run`.
- Real publish runs (`--mode roundtrip`) only when the matching `delete-<platform>` skill exists and has been verified at least once.
- Dry-run uses each `publish-*` SKILL.md's `## Dry-run` subsection (stops before final Publish click).

## Don't list

- Don't write per-run logs to `logs/`. The action log is the only run-level log.
- Don't auto-script flows yet. `/scriptify-flow` is a placeholder that calls `scripts/action-log-summarize.mjs`.
- Don't create per-brand subfolders under `.claude/skills/`. Skills stay brand-agnostic and read brand YAML.
- Don't take screenshots to disk except on error (action log path).
- Don't try to auto-login. If a session expires → return an error pointing the user at `/first-time-login`.
- Don't `pkill chrome` or delete `SingletonLock`. Use `/unlock-browser`.

## Playwright split (see OPERATING_RULES §11)

- Writes → MCP. Reads (bulk own-account scraping) → `scripts/scrape-*.mjs`. Profile dir is shared, never concurrent.
- Scrape script writes `data/scrape-logs/<run-id>-<platform>.jsonl`. Action log stays MCP-only.
