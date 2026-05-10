---
name: delete-x
description: Delete an X (Twitter) post by URL.
---

> Common rules: `docs/OPERATING_RULES.md`. X-specific deletion only.

## Input
- `target_url`: `https://x.com/<handle>/status/<id>`.

## Output
```json
{ "deleted": true, "verified_gone": true }
```

## Steps

1. `browser_navigate` → `target_url`.
2. Click the "..." caret on the tweet (visible at top-right of the tweet card).
3. Click "Delete" in the popup.
4. Confirm in the second modal.
5. Wait for the "Your post was deleted" toast.
6. Verify removal:
   - `browser_navigate` → `target_url`.
   - Look for the "Hmm...this page doesn't exist" marker.
7. `mcp__playwright__browser_close`.

## Quirks

- "..." appears only on tweets you own. If the page loads but the caret is missing, you are not signed in as the owner — return `{ "error": "delete_no_permission" }`.
- Bookmark / mute options live in the same dropdown — read item text before clicking, do not rely on position.
- Replies and quote-retweets of the deleted tweet remain (X behavior); the round-trip test only cares about the original tweet URL.

## Failure handling

- Already gone → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.

## Don'ts

- Do not call other skills.
- Do not "Hide replies" or "Mute" instead of delete.
