---
description: Phase 2 — actually publish. Reads draft JSON, runs publish-* in main session sequentially, logs every Playwright call.
argument-hint: "draft:<id>  or  [platforms] [caption / image_path]"
---

Two modes:

- **A. Draft mode (preferred)**: `draft:<id>` loads `reports/drafts/<brand>/<id>.json` written by `/draft-post`. The user has already confirmed.
- **B. Direct mode**: when the user explicitly says "publish directly, no draft". Compose from args + channel context, write a `<id>-direct` draft for traceability, then publish.

> Why no subagents: Playwright MCP cannot reach a subagent's browser session. `publish-*` runs in the main session, sequential per platform, `browser_close` between platforms.

## Action logging (orchestrator's job)

For every `mcp__playwright__browser_*` call during this command, append one line to `data/action-logs/<run-id>.jsonl` and update the matching `data/runs/<run-id>.meta.json`. Skills do not log themselves.

Run id format: `YYYYMMDD-HHMMSS-<rand4>`. Generate at the start of this command. Schema: see `docs/ACTION_LOG.md`.

## Mode A: draft:<id>

1. Load `reports/drafts/<brand>/<draft_id>.json`. Not found → `{ "error": "draft <id> not found" }`.
2. For each `local_image_path` / `local_video_path` in the drafts → run `local-reader.resolve_asset_path`. Any miss → abort the whole batch, reply with the missing path.
3. Validate the pending-confirmation: read `data/pending-confirmations.json`, find the entry for `<draft_id>`. If it has expired → reply: "Draft <id> expired. Re-run /draft-post." If missing entirely → still proceed (terminal-mode invocation may not have a pending entry).
4. For each platform in the draft, sequentially:
   - Read `.claude/skills/publish-<platform>/SKILL.md` + `docs/OPERATING_RULES.md` §5.
   - Call Playwright MCP per the SKILL.md steps (and wrap each call into the action log).
   - Resolve mid-flow noise per OPERATING_RULES §5; do not surface to channel.
   - When done, `mcp__playwright__browser_close` before the next platform.
   - Collapse to one of three end states:
     - `{ "status": "success", "post_url": "..." }`
     - `{ "status": "needs_verify", "post_url": null, "error": "url_extraction_failed", "note": "post may have published, please verify manually" }`
     - `{ "status": "failed", "error": "...", "step_failed": "..." }`
5. After all platforms, write one report per platform: `reports/posts/<brand>/<draft_id>-<platform>.md`:

   ```markdown
   # <platform> post — <draft_id>

   - status: ✅ success | ⚠️ needs_verify | ❌ failed
   - post_url | error: ...
   - note: <only for needs_verify>
   - published_at: <ISO>
   - run_id: <run_id>           # links to action log
   - caption:
     <caption>
   - hashtags: #a #b
   - media: <local path>
   ```

6. Update `data/pending-confirmations.json` — remove the `<draft_id>` entry (consumed).

7. Update `data/runs/<run-id>.meta.json` with the final per-platform `outcomes` array and `status: success | partial | failed`.

8. Reply once with the final result (channel sessions: TG `reply`; terminal: main-session text). Plain text, no markdown:

   ```
   ✅ posted
   IG: https://www.instagram.com/p/...
   FB: https://www.facebook.com/.../posts/...

   ⚠️ needs verify (Publish clicked but URL not captured)
   X: please open https://x.com/<handle>

   ❌ failed
   YT: channel verification required → verify in YT Studio and retry

   reports: reports/posts/<brand>/<draft_id>-*.md
   action log: data/action-logs/<run_id>.jsonl
   ```

   - Show only the sections that have entries.
   - Do not send mid-flow updates. One final reply per run.

## Mode B: direct publish

1. Compose `platforms` / `caption` / `hashtags` / media path from args + channel message + uploaded media.
2. Generate `draft_id = YYYYMMDD-HHMMSS-direct`. Write `reports/drafts/<brand>/<draft_id>.json` immediately so the run is traceable.
3. Continue with steps 3-8 of Mode A.

## Platform → skill table

| platform | skill | required input |
|---|---|---|
| `facebook` | `publish-facebook` | caption, hashtags, mode, local_image_path / local_video_path |
| `instagram` | `publish-instagram` | same |
| `x` | `publish-x` | caption, hashtags, mode, image / video optional |
| `threads` | `publish-threads` | same |
| `youtube` | `publish-youtube` | title, description, tags, local_video_path, format, visibility |
| `tiktok` | `publish-tiktok` | caption, hashtags, local_video_path, visibility |

## Common discipline

- `mcp__playwright__browser_close` between platforms and once at the end (extra closes are no-ops).
- One run id covers the whole batch — do not generate a new id per platform.
- If the action log directory does not exist, create it before the first call.

## Verification

- [ ] Each requested platform yields one of `success` / `needs_verify` / `failed`.
- [ ] One `reports/posts/<brand>/<draft_id>-<platform>.md` per platform.
- [ ] `data/action-logs/<run_id>.jsonl` and `data/runs/<run_id>.meta.json` written.
- [ ] Pending-confirmation entry removed.
- [ ] One final channel reply, partitioned by status.
- [ ] Browser closed.

## Don'ts

- Do not spawn subagents to run Playwright — they cannot reach the browser.
- Do not parallelize platforms — single browser instance per brand.
- Do not fabricate `post_url` — return `needs_verify` when extraction fails.
- Do not skip the per-platform report — that's the only audit trail besides the action log.
- Do not re-draft — the draft has already been confirmed.
- Do not surface mid-flow noise to the channel (see OPERATING_RULES §5).
