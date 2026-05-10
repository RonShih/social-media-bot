---
name: publish-tiktok
description: Upload a short video to TikTok via TikTok Studio. Video-only.
---

> Common rules: `docs/OPERATING_RULES.md`. TikTok-specific quirks only.

## Input
- `caption`: post text + hashtags merged (TikTok caption + tags share the 4000-char box, but draft-tiktok keeps caption short).
- `hashtags`: list of strings — append after caption with single spaces (the SKILL appends, drafting does not duplicate).
- `local_video_path`: absolute path.
- `visibility`: `public` | `friends` | `private` (default `public`).

## Output
```json
{ "post_url": "https://www.tiktok.com/@<handle>/video/<id>", "platform": "tiktok" }
```

## Steps

1. `browser_navigate` → `https://www.tiktok.com/tiktokstudio/upload`.
2. `browser_file_upload` with the video. Wait until the inline preview renders (can take 30-90s for HD).
3. Click into the description textarea, type `caption + " " + hashtags.join(" ")`.
4. Cover: leave auto unless `extra.cover_path` is provided.
5. "Who can watch this video" → set per `visibility`.
6. "Allow users to" — leave defaults (comment / duet / stitch).
7. Click "Post".
8. Wait for the "Your video is being uploaded" → "Video posted" sequence in the corner toast.
9. Extract the post URL.

## Quirks

- Description text input: TikTok Studio uses a `contenteditable` div; `browser_type` with the element ref works, `evaluate(elem.value = ...)` does not.
- Hashtag autocomplete: typing `#xxx` triggers a dropdown. After typing the tag, press Escape to dismiss the dropdown — otherwise the next hashtag's first character may auto-complete to a different tag.
- "Drafts saved" toasts are noise; ignore.
- Re-auth: TikTok occasionally throws a "Verify it's you" challenge mid-upload (CAPTCHA or SMS). This is a hard stop — return `{ "error": "tiktok challenge required", "step_failed": "verify_human" }`.

## URL extraction

After the "Video posted" toast, click the "View" link in that toast (it goes straight to the public URL). Capture the URL from the page that opens (`page.url()` via `browser_evaluate`).

Fallback: navigate to `socials.tiktok.url`, read the first video tile (`a[href*="/video/"]`).

If both fail → `{ "post_url": null, "error": "url_extraction_failed" }`.

## Dry-run

- Stop after step 6 (all metadata filled). Do not click Post.
- Studio does not have a "Save draft" button on this screen for the web upload flow — the only safe exit is browser-back, which discards the in-progress upload. Confirm this is the right behavior with the user; otherwise dry-run for TikTok is more disruptive than other platforms (no leftover draft).
- `browser_close`.
- Return `{ "status": "dry_run_ok", "draft_residue": "no — in-progress upload was discarded" }`.

## Delete (called by `delete-tiktok`)

TikTok deletion is immediate from the user-facing perspective but may require re-auth. If `delete-tiktok` returns `delete_failed`, the orchestrator surfaces it to the user — do not retry silently.
