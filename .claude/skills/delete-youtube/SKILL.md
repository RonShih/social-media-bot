---
name: delete-youtube
description: Move a YouTube video to trash via Studio. Soft delete — the video is recoverable for 30 days.
---

> Common rules: `docs/OPERATING_RULES.md`. YT-specific deletion only.

## Input
- `target_url`: `https://youtu.be/<id>` or `https://www.youtube.com/watch?v=<id>` or `https://youtube.com/shorts/<id>`. Extract `<id>` to navigate Studio.

## Output
```json
{ "deleted": true, "verified_gone": true }
```

`verified_gone: true` means re-fetching `target_url` shows "Video unavailable" or "This video has been removed". A hard 404 is **not** expected — YouTube keeps the URL responding for 30 days.

## Steps

1. Extract video id from `target_url`.
2. `browser_navigate` → `https://studio.youtube.com/video/<id>/edit`.
3. Click the "Options" / three-dot menu in the top toolbar (or right-click the video row in the videos list).
4. Click "Delete forever" → "Move to trash". (UI labels: Studio shifted from "Permanently delete" to "Move to trash" mid-2024; both end up the same.)
5. Confirm in the modal — tick the "I understand..." checkbox if present, then confirm.
6. Wait for the "Video deleted" / "Moved to trash" toast.
7. Verify:
   - `browser_navigate` → `target_url`.
   - Look for "Video unavailable" or "This video has been removed".
   - Set `verified_gone` accordingly.
8. `mcp__playwright__browser_close`.

## Quirks

- YT Studio's toolbar varies between Shorts and long-form videos. For Shorts, the three-dot menu is on the video row in `https://studio.youtube.com/channel/<channel_id>/videos/short`.
- Studio occasionally requires re-auth for destructive actions — surfaces as a Google login prompt mid-flow. Return `{ "error": "youtube_reauth_required", "step_failed": "delete_confirm" }`.

## Failure handling

- Already gone → `{ "deleted": true, "verified_gone": true, "note": "already gone" }`.
- 30-day grace period: the round-trip test does not need to wait for permanent deletion; "Video unavailable" page is sufficient.

## Don'ts

- Do not unpublish (`Save → Visibility: Private`) instead of deleting — the round-trip test would falsely report success while the video lingers in your channel.
- Do not call other skills.
