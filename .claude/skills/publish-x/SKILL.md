---
name: publish-x
description: Publish a single X (Twitter) post — text + optional image or video — via Playwright.
---

> Common rules: `docs/OPERATING_RULES.md`. X-specific quirks only.

## Input
- `caption`: post text. Total `caption + hashtags` must be ≤ 280 chars (drafting enforces this; do not silently truncate here — return an error if over).
- `hashtags`: list of strings (appended with single spaces).
- `mode`: `post` (text + optional image) | `video`.
- `local_image_path`: optional for `mode: post`.
- `local_video_path`: required for `mode: video`.

## Output
```json
{ "post_url": "https://x.com/<handle>/status/...", "platform": "x" }
```

## Common steps

1. `browser_navigate` → `https://x.com/home`.
2. Click the compose button (left rail, the feather icon) or press the keyboard shortcut `n`.
3. Type `caption + " " + hashtags.join(" ")` into the composer text area.
4. (If media) Click the image / GIF icon, then `browser_file_upload`.
5. Wait for the upload thumbnail / video preview.
6. Click "Post" / "發布".
7. Wait for the home feed to refresh and the new post to appear at the top.
8. Extract the post URL.

### `mode: video`

- Wait time after upload is longer (encoding). Allow up to 60s on the preview render.
- X rejects videos > 2:20 by default; assume drafting respected the brand's video guidelines.

## Quirks

- "Add a description" / alt-text dialog may pop up after upload — click "Skip" / X. Do not write alt text unless `extra.alt` is provided.
- Free-tier compose may show "Subscribe to X Premium" upsell — close it.
- After "Post", the composer modal closes; the URL is not in the modal — fetch from the home feed (next step).

## URL extraction

After clicking Post, the new tweet appears at the top of `https://x.com/home`. Use `browser_evaluate`:

```js
(handle) => {
  const links = [...document.querySelectorAll('a[href*="/status/"]')];
  const own = links.find(a => a.getAttribute('href').toLowerCase().includes(`/${handle.toLowerCase()}/status/`));
  return own ? new URL(own.getAttribute('href'), location.origin).href : null;
}
```

Pass the brand's `socials.x.handle`. Retry once after 3s if null. Two failures → `{ "post_url": null, "error": "url_extraction_failed" }`.

## Dry-run

- Stop after step 5 (preview rendered). Do not click Post.
- Press Escape to close the composer, accept the discard prompt.
- `browser_close`.
- Return `{ "status": "dry_run_ok" }` or the failure form.
