---
description: Validate publish flows. dry-run (stop before final Publish) or roundtrip (real publish + delete + verify).
argument-hint: "<platform[,platform...]> [--source single|plan|url] [--draft <id>] [--plan <YYYY-Www> --slot <id>] [--url <ref>] [--mode dry-run|roundtrip]"
---

Pre-flight (default `--mode dry-run`) or full round-trip validation. Main session, sequential per platform, `browser_close` between.

## Action logging

Same as `/publish-now`: every Playwright call is wrapped into `data/action-logs/<run-id>.jsonl` and `data/runs/<run-id>.meta.json`. Set `meta.mode` to `dry-run` or `roundtrip`.

## Modes

### `--mode dry-run` (default)

1. Resolve inputs:
   - `--source single --draft <id>`: load `reports/drafts/<brand>/<id>.json`.
   - `--source plan --plan <YYYY-Www> --slot <id>`: load `reports/plans/<brand>/<plan>/plan.json`, find the slot, materialize draft-like fields. Synthesize `draft_id = <plan>-<slot>-test`.
   - `--source url <url>`: spawn `fetch-reference` subagent first, then run all 6 `draft-<platform>` subagents in parallel to produce a draft. Synthesize `draft_id = <YYYYMMDD-HHMMSS>-test`.
2. For each requested platform sequentially:
   - Read `.claude/skills/publish-<platform>/SKILL.md`'s `## Dry-run` subsection.
   - Drive the steps until the stop point (preview rendered / metadata filled, before final Publish).
   - Close the composer cleanly (per SKILL.md cleanup), then `browser_close`.
   - Write `reports/posts/<brand>/<draft_id>-<platform>.dry-run.md` with status / step_failed / error.
3. Reply once with the aggregate result. Plain text:

   ```
   📝 dry-run <draft_id>
   facebook: dry_run_ok
   instagram: dry_run_failed at upload-image: file_upload_timeout
   x: dry_run_ok
   threads: dry_run_ok

   reports: reports/posts/<brand>/<draft_id>-*.dry-run.md
   action log: data/action-logs/<run_id>.jsonl
   ```

### `--mode roundtrip`

Real publish + delete + verify. Hard requirements before running:

- `delete-<platform>` skill must exist for every requested platform (all 6 ship with this repo).
- The user must have invoked the command with `--mode roundtrip` explicitly. Default mode is dry-run; never silently upgrade.

Per platform sequence:

1. Run `publish-<platform>` exactly as `/publish-now` would (full SKILL.md flow, real Publish click).
2. Capture `post_url` and the publish status.
   - On `needs_verify` (URL extraction failed) → record, **do not delete** (no address). Mark roundtrip status `needs_verify`. Continue to next platform.
   - On `failed` → record, do not delete. Mark `publish_failed`. Continue.
   - On `success` → continue to delete.
3. Run `delete-<platform>` with `target_url = post_url`.
4. Capture `deleted`, `verified_gone`.
5. Determine the platform's roundtrip status:
   - `deleted && verified_gone` → `success`.
   - `deleted && !verified_gone` → `verify_failed` (post may still be visible; YouTube's 30-day trash counts as verified-gone if the URL shows "Video unavailable").
   - `!deleted` → `delete_failed` (orchestrator surfaces; no retry).
6. `browser_close` before next platform.
7. Write `reports/posts/<brand>/<draft_id>-<platform>.roundtrip.md` with status / post_url / deleted / verified_gone / notes.

Reply once with the aggregate result. Plain text:

```
🔁 roundtrip <draft_id>
facebook: ✅ success (published, deleted, verified gone)
threads: ⚠️ verify_failed (deleted but URL still resolves)
youtube: ❌ publish_failed (channel verification required)

reports: reports/posts/<brand>/<draft_id>-*.roundtrip.md
action log: data/action-logs/<run_id>.jsonl
```

## YouTube round-trip note

YT delete is "move to trash" with a 30-day recovery window. The `verified_gone` check accepts a "Video unavailable" page as gone — a hard 404 will not happen. This is the documented expectation; do not flag YT roundtrip as `verify_failed` purely because the URL still responds with HTTP 200.

## TikTok round-trip note

TikTok occasionally requires re-auth on delete (CAPTCHA / SMS). Surface `delete_failed` to the user with the underlying reason; do not retry silently and do not attempt to solve the challenge.

## Verification

- [ ] One `*.dry-run.md` or `*.roundtrip.md` per platform.
- [ ] One final reply (no mid-flow updates).
- [ ] Action log + meta JSON written.
- [ ] Browser closed.
- [ ] In roundtrip mode, every `success` row corresponds to a real publish that was deleted and verified gone.

## Don'ts

- Do not parallelize platforms.
- Do not auto-upgrade dry-run to roundtrip.
- Do not chain `publish-*` and `delete-*` from within a skill — the orchestrator (this command) is responsible.
- Do not silently retry `delete-*` on re-auth errors.
- Do not skip writing the report file even on early failure — that's the audit trail.
