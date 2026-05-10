---
description: Execute scheduled slots from the active weekly plan. Sequential per slot, action-logged, two-stage gate honored.
argument-hint: "[--week <YYYY-Www>] [--day today|<weekday>] [--slot <slot_id>]"
---

Run the slots scheduled for a given day from `reports/plans/<brand>/<iso_week>/plan.json`. Same publish discipline as `/publish-now`: main session, sequential, `browser_close` between platforms, action-logged.

## Steps

1. Resolve `iso_week` (default: current). Resolve target slots:
   - `--slot <slot_id>` → exactly that slot.
   - `--day today` → all slots whose `weekday` matches today (in the brand's primary timezone — defaults to system local) AND `time_local` is ≤ now (catch up on missed earlier slots).
   - `--day <weekday>` → all slots with that weekday, regardless of time.
   - Default (no flags) → `--day today`.
2. Filter out slots whose `status` is already `posted`.
3. If running in a channel session (TG / Line) and `data/pending-confirmations.json` does not contain the matching draft id → **send a preview reply first**, write a pending-confirmation entry with `expires_at = now + 5min`, and stop. The user replies `ok` to proceed.
   - In terminal sessions, the user invoked the command intentionally; skip the gate.
4. Generate run id; set `meta.mode = "publish-from-plan"`. Initialize action log.
5. For each scheduled slot:
   - Materialize a draft JSON at `reports/drafts/<brand>/<draft_id>.json` (where `draft_id = slot.draft_id` — usually `weekly-<slot_id>`). This makes the slot indistinguishable from a regular `/publish-now draft:<id>` run for downstream tooling.
   - Run `publish-<slot.platform>` per its SKILL.md. Wrap every Playwright call in the action log.
   - Capture `post_url` (or `needs_verify` / failure).
   - Update the in-memory plan: `Schedule[slot_id].status = posted | failed | needs_verify`, `posted_url`, `posted_at = ISO`.
   - Write `reports/posts/<brand>/<draft_id>-<platform>.md` (same format as `/publish-now`).
   - `mcp__playwright__browser_close` before next slot.
6. Persist updated plan: write `plan.json`, then re-export `plan.xlsx` via `weekly-plan-export`.
7. Update `data/runs/<run-id>.meta.json`: set `outcomes`, final `status`.
8. Remove consumed `pending-confirmations` entries (if any).
9. Reply once with the result. Plain text:

   ```
   ✅ posted from plan (<iso_week>, <day>)
   IG mon 12:30: https://www.instagram.com/p/...
   FB tue 11:00: https://www.facebook.com/.../posts/...

   ⚠️ needs verify
   X tue 09:00: please open https://x.com/<handle>

   ❌ failed
   YT: skipped (channel verification required)

   plan: reports/plans/<brand>/<iso_week>/plan.json
   reports: reports/posts/<brand>/weekly-<iso_week>-*-*-*.md
   action log: data/action-logs/<run_id>.jsonl
   ```

## Catch-up policy

If `--day today` finds no due slots → reply: "no slots due for today on plan <iso_week>. Next slot: <next slot_id at HH:MM>".

If multiple slots are due (e.g. the bot was offline for hours) → process them in `time_local` order, sequentially. Do not parallelize.

## Verification

- [ ] Each processed slot ended in one of `success | needs_verify | failed`.
- [ ] `plan.json` updated with status / posted_url / posted_at for each.
- [ ] `plan.xlsx` regenerated from updated json.
- [ ] One report file per slot.
- [ ] Action log + meta JSON written.
- [ ] One final reply.
- [ ] Browser closed.

## Don'ts

- Do not process slots out of time order.
- Do not parallelize platforms.
- Do not silently re-publish a slot whose status is already `posted` — skip with a note.
- Do not auto-bypass the two-stage gate in channel sessions.
- Do not modify any other ISO week's plan.
