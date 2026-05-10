# social-media-bot

Multi-brand social-media operator for Facebook, Instagram, X, Threads, YouTube, TikTok. LLM-driven via Claude Code, browser-driven via Playwright MCP. No platform APIs, no cloud, no secrets in repo.

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
- `templates/CLAUDE.user.md` — copy into `~/.claude/CLAUDE.md` on the user's machine to get the bot-session UX (ack-first, plain text, two-stage gate).
- `docs/` — operating rules, weekly-plan reference, action-log schema.
- `scripts/` — Node helpers (`plan-export.mjs`, `plan-import.mjs`, `action-log-summarize.mjs`).
- `media/assets/<brand>/` — image / video library; `inbox/` for Telegram-uploaded files.
- `reports/` — drafts, posts, weekly plans (per brand).
- `data/action-logs/`, `data/runs/` — JSONL action logs + run metadata.
- `browser_profiles/<brand>/` — Chromium persistent profile (gitignored).

## Multi-brand

- One repo, many brand profiles under `config/brands/`.
- Switch active brand by editing `config/active-brand` or exporting `BRAND=<slug>`.
- Each brand has its own `browser_profiles/<brand>/` (separate logins).
- Skills are brand-agnostic; everything brand-specific reads from the brand YAML.

## Telegram / Line bot integration

This repo does not run a bot process. It ships a `templates/CLAUDE.user.md` to copy into the user's `~/.claude/CLAUDE.md`. When the user wires Telegram (or Line) into Claude Code as a channel, that template makes Claude:

- React 👀 immediately on every inbound message.
- Reply in plain text, no markdown.
- Run `/draft-post` and `/weekly-plan` as preview-only.
- Wait for "ok" / "go" / "yes" / explicit slash command before `/publish-now`.

See `docs/HOW_TO_USE.md` for the full operator playbook.
