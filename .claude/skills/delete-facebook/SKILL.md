---
name: delete-facebook
description: Delete a Facebook post by its public URL. Used by /test-roundtrip cleanup.
---

> Common rules: `docs/OPERATING_RULES.md`. FB-specific deletion only.

## Input
- `target_url`: the post URL returned by `publish-facebook` (`https://www.facebook.com/.../posts/pfbid...` or `/reel/<id>/`).

## Output
```json
{ "deleted": true, "verified_gone": true }
```

`verified_gone: true` means a re-fetch of `target_url` shows "This content isn't available right now" / not-found state. `false` means the URL still resolves (deletion may need more time, or a manual step is required).

## Steps

1. `browser_navigate` → `target_url`.
2. Click the "..." menu on the post (top-right of the post card).
3. Select "Move to trash" / "移至垃圾桶".
4. Confirm in the modal ("Move post to trash").
5. Wait for the success toast.
6. Verify removal:
   - `browser_navigate` → `target_url` again.
   - Inspect the page for "This content isn't available" / "內容無法顯示" / 404 markers via `browser_evaluate`.
   - Set `verified_gone` accordingly.
7. `mcp__playwright__browser_close`.

## Quirks

- For Reels (`/reel/<id>/`), the "..." menu lives inside the Reel viewer overlay, not on a feed card. Open the Reel first.
- Trashed posts can be restored within 30 days from `https://www.facebook.com/your-trash/`. The round-trip test only cares that the post is no longer publicly visible.

## Failure handling

- Post no longer exists (already deleted) → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.
- "..." menu missing (post is on a wall the bot can't moderate, e.g. group post) → `{ "error": "delete_no_permission", "step_failed": "open_menu" }`.
- Network / Playwright error → `{ "error": "<reason>", "step_failed": "<step>" }`. Do not retry blindly; the orchestrator will surface to the user.

## Don'ts

- Do not "move to archive" instead of "trash" — archive keeps the post visible to the page admin and the round-trip test would falsely report not-deleted.
- Do not delete by post id alone — always navigate to the URL first to confirm it's a post you own.
- Do not call other skills.
