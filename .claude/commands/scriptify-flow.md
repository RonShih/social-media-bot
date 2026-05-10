---
description: Render a human-readable replay of an action-log run. Placeholder for v2 codegen — currently calls action-log-summarize.mjs.
argument-hint: "<run-id>"
---

Print the step-by-step trace of a run from `data/action-logs/<run-id>.jsonl` + `data/runs/<run-id>.meta.json`.

## Steps

1. If `<run-id>` is missing → reply with usage hint and `ls -1t data/runs/ | head -10` to show the most recent runs.
2. Run:

   ```bash
   node scripts/action-log-summarize.mjs <run-id>
   ```

3. Stream the output back to the user (terminal stdout is fine; for channel sessions, post the first ~40 lines and link the action-log file path).

## Why a placeholder

The plan goal for `/scriptify-flow` is to convert a series of stable action-log runs into a reusable Playwright `.mjs` script — replay without LLM reasoning. That codegen is v2.

Until then, this command renders the existing log so the user can:

- Triage a `partial` run (find the exact step that failed).
- Spot selector drift across runs (search the output for the same `step_label`).
- Confirm a flow is stable enough to be worth converting later.

## Don'ts

- Do not generate actual Playwright code yet — surface "v2 feature, not implemented" if the user asks.
- Do not modify the action log or meta JSON.
- Do not attempt a "best-effort" code emission — wait for the v2 design.
