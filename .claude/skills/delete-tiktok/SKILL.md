---
name: delete-tiktok
description: Delete a TikTok video via Studio.
---

> Common rules: `docs/OPERATING_RULES.md`. TikTok-specific deletion only.

## Input
- `target_url`: `https://www.tiktok.com/@<handle>/video/<id>`.

## Output
```json
{ "deleted": true, "verified_gone": true }
```

## Steps

1. `browser_navigate` → `https://www.tiktok.com/tiktokstudio/content`.
2. Find the row matching the target video. The row id ends with the video id; otherwise match on the post URL.
3. Click the "..." menu on that row.
4. Click "Delete".
5. Confirm in the modal.
6. Wait for the row to disappear from the content list.
7. Verify removal:
   - `browser_navigate` → `target_url`.
   - Look for the "Video currently unavailable" marker.
8. `mcp__playwright__browser_close`.

## Quirks

- TikTok prompts re-auth on destructive actions roughly every 30 days. If a "Verify it's you" / SMS / CAPTCHA step appears → return `{ "error": "tiktok_reauth_required", "step_failed": "delete_confirm" }`. Do not attempt to solve the CAPTCHA.
- Newly published videos sometimes do not appear in the content list for 30-60 seconds. The orchestrator should retry the navigation once after a 30-second wait if the row is missing.

## Failure handling

- Already gone → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.

## Don'ts

- Do not "Set as private" instead of delete — the round-trip test would falsely succeed.
- Do not call other skills.
- Do not retry indefinitely on re-auth — surface to user.
