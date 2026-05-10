---
name: delete-threads
description: Delete a Threads post by URL.
---

> Common rules: `docs/OPERATING_RULES.md`. Threads-specific deletion only.

## Input
- `target_url`: `https://www.threads.net/@<handle>/post/<id>`.

## Output
```json
{ "deleted": true, "verified_gone": true }
```

## Steps

1. `browser_navigate` → `target_url`.
2. Click the "..." on the post (top-right area of the thread card).
3. Click "Delete" in the popup.
4. Confirm in the second modal.
5. Verify removal:
   - `browser_navigate` → `target_url`.
   - Look for "Sorry, we couldn't find this thread." marker.
6. `mcp__playwright__browser_close`.

## Quirks

- Threads deletion takes 1-3 seconds to propagate; allow a brief wait before the verify step.
- Replies to the deleted post become orphaned — Threads handles this internally; the round-trip test does not care.

## Failure handling

- Already gone → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.

## Don'ts

- Do not call other skills.
