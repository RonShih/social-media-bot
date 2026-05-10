---
name: test-roundtrip
description: Validate a publish flow end-to-end. Two modes — dry-run (stop before final Publish) or roundtrip (real publish + delete + verify).
---

> Common rules: `docs/OPERATING_RULES.md`. Default mode for the `/test-roundtrip` command is `dry-run`.

## Input
- `platforms`: list of platform keys (`facebook`, `instagram`, `x`, `threads`, `youtube`, `tiktok`).
- `mode`: `dry-run` (default) | `roundtrip`.
- One of:
  - `draft_id`: existing draft from `reports/drafts/<brand>/<draft_id>.json`.
  - `plan`: `{ iso_week: "2026-W19", slot_id: "..." }` — pull from a weekly plan.
  - `url`: external URL — caller is responsible for running `fetch-reference` first; pass the resulting reference and a draft id of `<YYYYMMDD-HHMMSS>-test`.

## Output

For `mode: dry-run`:
```json
{
  "platforms": [
    { "platform": "facebook", "status": "dry_run_ok" },
    { "platform": "x", "status": "dry_run_failed", "step_failed": "...", "error": "..." }
  ]
}
```

For `mode: roundtrip`:
```json
{
  "platforms": [
    {
      "platform": "facebook",
      "status": "success",
      "post_url": "https://...",
      "deleted": true,
      "verified_gone": true
    },
    {
      "platform": "youtube",
      "status": "publish_failed",
      "error": "channel verification required"
    }
  ]
}
```

## Steps

1. Resolve inputs. If `draft_id` is given, load the draft. If `plan` is given, read `reports/plans/<brand>/<iso_week>/plan.json`, find the slot, materialize the same fields a draft would carry. If `url` is given, expect caller to have done the fetch-reference.
2. For each platform sequentially (the orchestrator owns sequencing; this skill describes the per-platform contract):

   ### `mode: dry-run`
   - Run `publish-<platform>` per its SKILL.md `## Dry-run` subsection.
   - Write a marker file: `reports/posts/<brand>/<draft_id>-<platform>.dry-run.md`:
     ```
     # <platform> dry-run — <draft_id>
     - status: dry_run_ok | dry_run_failed
     - step_failed: ...        # only on failure
     - error: ...              # only on failure
     - run_id: <run_id>
     - tested_at: <ISO>
     ```
   - `mcp__playwright__browser_close` between platforms.

   ### `mode: roundtrip`
   - Run the full `publish-<platform>` (real publish).
   - Capture `post_url`. If `needs_verify` (URL extraction failed) → record and skip the delete step (we can't delete what we can't address). Marker file written; `deleted: null, verified_gone: null`.
   - If publish failed → record `publish_failed`, skip delete.
   - On real `success`:
     - Pass `post_url` to `delete-<platform>` as `target_url`.
     - Capture `deleted`, `verified_gone` from the delete skill.
   - Write `reports/posts/<brand>/<draft_id>-<platform>.roundtrip.md`:
     ```
     # <platform> roundtrip — <draft_id>
     - status: success | needs_verify | publish_failed | delete_failed | verify_failed
     - post_url: ...
     - deleted: true | false | null
     - verified_gone: true | false | null
     - run_id: <run_id>
     - tested_at: <ISO>
     - notes: ...
     ```
   - `mcp__playwright__browser_close` between platforms.

3. Return the aggregate JSON to the caller.

## URL passing

The orchestrator (`/test-roundtrip` command) holds `post_url` and feeds it to `delete-<platform>` — this skill does not call other skills. Skill-to-skill calls are forbidden.

## Don'ts

- Do not call `publish-*` and `delete-*` from inside this skill — the orchestrator chains them.
- Do not skip `mcp__playwright__browser_close` between platforms — the next platform will hit a profile lock.
- Do not loop the delete step. One try; on failure surface to the user.
- Do not run `mode: roundtrip` for a platform whose `delete-<platform>` skill has not been verified at least once — the orchestrator gates this.
- Do not return `success` if `verified_gone: false` in roundtrip mode — that indicates the post is still live; mark `verify_failed` instead.
