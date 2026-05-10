---
name: publish-facebook
description: Publish a Facebook post (image or video / Reel) via Playwright. Reads brand from active YAML.
---

> Common rules: `docs/OPERATING_RULES.md`. This file only documents FB-specific quirks.

## Input
- `caption`: post text.
- `hashtags`: list of strings, appended after caption with one blank line.
- `mode`: `post` (image) | `video` (Reel or feed video).
- `local_image_path`: absolute path (required for `mode: post`).
- `local_video_path`: absolute path (required for `mode: video`).

## Output
```json
{ "post_url": "https://...", "platform": "facebook" }
```

## Common steps

1. `browser_navigate` → `socials.facebook.url` from active brand YAML.
2. Switch to page identity if a "Switch to page" / "立即切換" banner is visible. If no banner, you are already on the page; do not click elsewhere — clicking the wrong identity posts as personal.
3. Open composer ("What's on your mind?" / "在想些什麼？").
4. Type `caption + "\n\n" + hashtags.join(" ")` into the composer text area.
5. Click "Photo / Video" / "相片／影片", then `browser_file_upload` with the asset.
6. Wait for the preview thumbnail to render.
7. Click "Post" / "發佈". Use `name: '發佈', exact: true` (or the exact en label) — partial match risks hitting "Boost post" / "加強推廣貼文" which also contains "發佈".
8. Handle post-publish dialogs (see Quirks).
9. Extract the post URL (see URL extraction).

### `mode: post` (image)

Step 5 → upload one image. Wait until the image thumbnail appears in the composer.

### `mode: video` (Reel / feed video)

- Reel (vertical) flow is a **three-stage dialog**: Create Post → Edit Reel → Reel Settings.
  - Caption typed in stage 1 carries over; do not re-edit it in later stages.
  - Click "Continue" / "繼續" through stages 1 and 2; click "Publish" / "發佈" on stage 3.
  - Do not expand or modify any field in stages 2 / 3 — defaults are fine.
- Feed video (horizontal / square) follows the standard composer; identical to the post flow except the upload is a video file.

## Quirks (only the ones that affect success)

- WhatsApp upsell dialog (appears 1-2 seconds after publish, title "讓用戶輕鬆與你聯絡" / "Make it easy for users to contact you") → click "稍後再說" / "Not now" or press Escape. **Never click "Add WhatsApp button"** — it interrupts the publish silently and the post does not go out.
- Identity-mismatch silent failure: if step 2 was skipped and you are still on the personal profile, FB will publish to the personal timeline without warning. Always re-check the identity badge before clicking Post.

## URL extraction

Preferred: Meta Business Suite. Read `socials.facebook.asset_id`, then `browser_navigate` to:

```
https://business.facebook.com/latest/posts/published_posts?asset_id=<asset_id>
```

Find the latest row, open its dropdown menu, read `getAttribute('href')` from the "View on Facebook" / "在 Facebook 查看貼文" item. Do not click — read the attribute.

Fallback: if `asset_id` is missing or Business Suite is inaccessible, return to the page profile and `browser_snapshot` every 10 seconds for up to 90 seconds, looking for a freshly added `/reel/<id>/` or `/posts/pfbid...` link.

If both fail → `{ "post_url": null, "error": "url_extraction_failed" }`. Do not invent a URL.

## Dry-run

- `mode: post`: stop after step 6 (preview rendered). Do not click Post.
- `mode: video` Reel: drive to Stage C "Reel Settings" and stop before clicking "Publish".
- Cleanup: click back / X to close the composer, accept "Discard changes?" prompt, then `browser_close`.
- Return `{ "status": "dry_run_ok" }` or `{ "status": "dry_run_failed", "step_failed": "...", "error": "..." }`.
