---
name: delete-instagram
description: Delete an Instagram Feed post or Reel by URL.
---

> Common rules: `docs/OPERATING_RULES.md`. IG-specific deletion only.

## Input
- `target_url`: `https://www.instagram.com/p/<id>/` or `/reel/<id>/`.

## Output
```json
{ "deleted": true, "verified_gone": true }
```

## Steps

1. `browser_navigate` → `target_url`.
2. Click the "..." (more options) icon on the post (top-right of the modal / page).
3. Click "Delete" / "刪除" in the popup menu.
4. Confirm in the second modal ("Delete post?" / "刪除貼文？").
5. Wait for the redirect (IG drops you back to the profile).
6. Verify removal:
   - `browser_navigate` → `target_url`.
   - Look for the "Sorry, this page isn't available." marker via `browser_evaluate`.
   - Set `verified_gone` accordingly.
7. `mcp__playwright__browser_close`.

## Quirks

- For Reels, the "..." menu is inside the Reels player overlay, not on a static page. May require hovering / clicking the player first.
- IG sometimes shows a 1-second delay between confirm and redirect — wait briefly before the verify step.
- "Save to drafts" is **not** deletion. Reject any flow that ends in drafts.

## Failure handling

- Already gone → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.
- "..." menu missing (e.g. archived post) → `{ "error": "delete_unreachable", "step_failed": "open_menu" }`.

## Don'ts

- Do not archive the post (different action — keeps it on the account).
- Do not call other skills.
