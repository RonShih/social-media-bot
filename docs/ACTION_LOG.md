# Action log

Every Playwright `mcp__playwright__browser_*` call made during `/publish-now`, `/publish-from-plan`, `/test-roundtrip`, or the metrics-scrape step of `/weekly-plan` is wrapped by the orchestrator and appended to `data/action-logs/<run-id>.jsonl`.

The skill itself does not log. Skills stay declarative; logging belongs to the command that invokes the skill.

## Run id

Format: `YYYYMMDD-HHMMSS-<rand4>`. Generated at the start of a command, used for both the JSONL file and the meta JSON.

## JSONL line schema

One JSON object per line (no trailing comma, no array wrap). All fields required unless marked optional.

```json
{
  "ts": "2026-05-09T12:34:56.789Z",
  "run_id": "20260509-123456-r4f2",
  "brand": "noirs-boxes",
  "platform": "facebook",
  "step_idx": 7,
  "step_label": "click-publish-button",
  "tool": "mcp__playwright__browser_click",
  "args": { "element": "Publish button", "ref": "button[name='發佈']" },
  "result": "ok",
  "duration_ms": 412,
  "screenshot": null,
  "note": null
}
```

| field | required | type | meaning |
|---|---|---|---|
| `ts` | yes | string (ISO-8601 UTC, ms precision) | server clock at call start |
| `run_id` | yes | string | shared across the whole command invocation |
| `brand` | yes | string | active brand slug |
| `platform` | yes | string \| null | target platform; null for non-platform calls (e.g. fetch-reference Layer 3) |
| `step_idx` | yes | integer | sequence within the run, starting at 0 |
| `step_label` | yes | string | human label tied to the SKILL.md step (e.g. `"upload-thumbnail"`) |
| `tool` | yes | string | full MCP tool name |
| `args` | yes | object | sanitized args. Captions trimmed to 200 chars; full caption goes in `reports/posts/...` |
| `result` | yes | `"ok"` \| `"err"` | call outcome |
| `duration_ms` | yes | integer | wall-clock time |
| `screenshot` | optional | string \| null | absolute path; populated only on `err` |
| `note` | optional | string \| null | freeform (e.g. `"WhatsApp dialog dismissed"`) |

## Run meta JSON

Sibling at `data/runs/<run-id>.meta.json`. One file per run:

```json
{
  "run_id": "20260509-123456-r4f2",
  "mode": "publish | dry-run | roundtrip | publish-from-plan | weekly-plan-review",
  "started_at": "2026-05-09T12:34:56.123Z",
  "ended_at": "2026-05-09T12:36:12.987Z",
  "brand": "noirs-boxes",
  "platforms": ["facebook", "instagram"],
  "draft_id": "20260509-123420",
  "status": "success | partial | failed",
  "outcomes": [
    {"platform": "facebook", "status": "success", "post_url": "https://..."},
    {"platform": "instagram", "status": "needs_verify", "post_url": null, "error": "url_extraction_failed"}
  ]
}
```

## Retention

- Append-only. The file is never rewritten or rotated automatically.
- Recommended manual archive: every quarter, move `data/action-logs/*.jsonl` and `data/runs/*.meta.json` into a dated tarball (e.g. `data/archive/2026Q2.tar.gz`) and clear the live folders.
- Do not delete logs without archiving — they are the audit trail and the input to future scriptification.

## Reading the log

`scripts/action-log-summarize.mjs <run-id>` pretty-prints a run as a step-by-step replay (label, tool, ok / err, duration). Useful for triage after a partial failure.

```bash
node scripts/action-log-summarize.mjs 20260509-123456-r4f2
```

## What the log is for

1. **Triage**: a `partial` run prints exactly which step failed.
2. **Selector evolution**: a sequence of identical `step_label`s with diverging `args.ref` reveals platform UI drift.
3. **Future scriptification**: once a flow has logged 3+ successful runs with stable selectors, `/scriptify-flow` will (in a future version) emit a Playwright `.mjs` script that replays the steps without LLM reasoning. Currently `/scriptify-flow` only renders the human-readable replay.

## What the log is not

- Not a metrics store (post likes / reach live in `data/stats-history/<brand>.json`).
- Not a TG chat history.
- Not a config audit trail (use git for that).
