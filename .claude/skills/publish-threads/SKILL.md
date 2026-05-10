---
name: publish-threads
description: Publish a Threads post (text, image, or video) via Playwright. Threads identity = Instagram identity.
---

> Common rules: `docs/OPERATING_RULES.md`. Threads-specific quirks only.

## Input
- `caption`: post text (≤ 500 chars).
- `hashtags`: list of strings (Threads recommends ≤ 1, appended after a space).
- `mode`: `post` (text + optional image) | `video`.
- `local_image_path` / `local_video_path`: optional / required per mode.

## Output
```json
{ "post_url": "https://www.threads.net/@<handle>/post/...", "platform": "threads" }
```

## Common steps

1. `browser_navigate` → `https://www.threads.net/`.
2. Verify you are signed in (Threads uses the Instagram session; if not signed in, the page redirects to a login wall — return `{ "error": "login expired, run /first-time-login" }`).
3. Click "What's new?" / 「有什麼新鮮事？」 to open the composer.
4. Type `caption + " " + hashtags.join(" ")` into the textarea.
5. (If media) Click the attachment icon (paperclip), then `browser_file_upload`.
6. Wait for the upload thumbnail.
7. Click "Post" / "發布".
8. Wait for the success state (composer closes, feed shows new post).
9. Extract the post URL.

## Quirks

- The composer text area is a `contenteditable` div, not an `<input>` — typing must go through `browser_type` with the element ref, not via `evaluate('elem.value = ...')`.
- Threads sometimes shows an Instagram-permission interstitial on first publish from a new device ("Allow Threads to use your Instagram identity?") — accept it once. Subsequent runs skip it.
- The "Reply control" dropdown defaults to "Anyone" — leave alone unless `extra.reply_control` is provided.

## URL extraction

After publish, navigate to `socials.threads.url` (e.g. `https://www.threads.net/@<handle>`). Read the first post in the profile grid:

```js
(handle) => {
  const a = document.querySelector(`a[href*="/@${handle}/post/"]`);
  return a ? new URL(a.getAttribute('href'), location.origin).href : null;
}
```

Wait up to 90 seconds for the profile to refresh. Two failures → `{ "post_url": null, "error": "url_extraction_failed" }`.

## Dry-run

- Stop after step 6 (media uploaded / preview shown). Do not click Post.
- Click the X to close the composer; accept any "Discard" prompt.
- `browser_close`.
- Return `{ "status": "dry_run_ok" }` or the failure form.
