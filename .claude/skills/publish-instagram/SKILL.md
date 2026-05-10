---
name: publish-instagram
description: Publish an Instagram Feed post (image or Reel) via Playwright. Reads brand from active YAML.
---

> Common rules: `docs/OPERATING_RULES.md`. IG-specific quirks only.

## Input
- `caption`: post text.
- `hashtags`: list of strings — appended after a blank line, on a fresh paragraph.
- `mode`: `post` (Feed photo) | `video` (Reel).
- `local_image_path` (required for `mode: post`).
- `local_video_path` (required for `mode: video`).

## Output
```json
{ "post_url": "https://www.instagram.com/p/...", "platform": "instagram" }
```

## Common steps

1. `browser_navigate` → `socials.instagram.url`.
2. Click the "Create" / "+" / 新增 button in the left rail.
3. Click "Post" (for image) or "Reel" (for video) per `mode`.
4. `browser_file_upload` with the asset.
5. (Image only) Click "Next" through crop / filter screens — leave defaults.
6. Type `caption + "\n\n" + hashtags.join(" ")` into the caption box.
7. Click "Share" / "分享".
8. Wait for the success toast / "Your post has been shared".
9. Extract the post URL (see below).

### `mode: video` (Reel)

- The upload step accepts `.mp4` reliably. `.mov` files often hang at "uploading" — if the asset is `.mov`, copy / rename to `.mp4` first via `cp <src.mov> <dst.mp4>` (no transcode needed; Instagram accepts the H.264 inside).
- Cover frame: leave default unless `extra.cover_path` is provided.
- "Share to Facebook" toggle: leave at the user's default — do not flip it.

## Quirks

- After clicking "Share" the modal closes with a brief toast; the new post URL is not shown directly. Use the URL extraction below.
- If a "Drafts" / "草稿" prompt appears mid-flow ("Save as draft?"), click "Discard" — drafts that linger pile up and confuse later runs.
- Cookie / notification permission popups → dismiss without clicking anything that toggles a setting.

## URL extraction

After the success toast, navigate to `socials.instagram.url` and read the first post tile in the profile grid. Use `browser_evaluate`:

```js
() => {
  const a = document.querySelector('article a[href*="/p/"], article a[href*="/reel/"]');
  return a ? a.getAttribute('href') : null;
}
```

Prepend `https://www.instagram.com` if the href is path-only. Do this within 90 seconds of publish; older posts shift the grid.

If the grid does not refresh (cache) → `browser_navigate` to the profile URL once more, wait 3s, retry. Two failures → `{ "post_url": null, "error": "url_extraction_failed" }`.

## Dry-run

- Stop after step 6 (caption typed, before clicking Share).
- Click X / "Discard" to dismiss the composer.
- `browser_close`.
- Return `{ "status": "dry_run_ok" }` or the failure form.
