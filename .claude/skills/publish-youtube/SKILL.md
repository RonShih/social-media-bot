---
name: publish-youtube
description: Upload a video to YouTube via Studio and fill metadata. Video-only.
---

> Common rules: `docs/OPERATING_RULES.md`. YouTube-specific quirks only.

## Input
- `title`: ≤ 100 chars.
- `description`: full description (first 150 chars are the SERP snippet).
- `tags`: list of strings (no `#` prefix — YT tags are bare).
- `local_video_path`: absolute path.
- `format`: `long` (regular) | `short` (≤ 60s vertical — YT auto-detects from aspect ratio + duration, but caller declares for sanity).
- `visibility`: `public` | `unlisted` | `private` (default `public`).

## Output
```json
{ "post_url": "https://youtu.be/...", "platform": "youtube" }
```

For Shorts the URL form is `https://youtube.com/shorts/<id>` — return whichever Studio gave us.

## Steps

1. `browser_navigate` → `https://studio.youtube.com/`.
2. Click "Create" → "Upload videos".
3. `browser_file_upload` with the video. Wait for the upload progress bar to start.
4. Fill metadata while uploading (Studio allows this in parallel):
   - Title: paste `title`.
   - Description: paste `description`.
   - Thumbnail: leave auto unless `extra.thumbnail_path` is provided (then upload it).
   - Playlist: skip unless `extra.playlist_id`.
   - Audience: tick "No, it's not made for kids" (the standard non-kids choice). Channel verification banner blocks "made for kids" — handle as below.
   - Show more → Tags: paste comma-separated `tags`.
5. Click "Next" through "Video elements" (skip cards / end screens unless `extra.cards`).
6. Click "Next" through "Checks" — wait for the spinner to finish.
7. Set visibility per input.
8. Click "Publish" / "Save".
9. Wait for the "Video published" / "Video saved" dialog.
10. Read the share URL from that dialog (Studio displays the short link `youtu.be/...` directly).

## Quirks

- Channel-verification gate: if the channel has not been verified for >15-min videos, the upload UI will silently truncate. Surfaces as a banner — return `{ "error": "channel verification required", "step_failed": "channel_verify" }`.
- Copyright / Content ID auto-scan can take 1-5 minutes. Studio still lets you publish; the scan continues in the background. Do not wait for it.
- The "Made for kids" toggle is required — do not skip step 4's audience field, or Publish stays grayed out.

## URL extraction

The "Video published" dialog shows the short URL — read it from the displayed text or the copy-link button's `data-clipboard-text` attribute. If the dialog auto-closes before reading, navigate to `https://studio.youtube.com/channel/<id>/videos` and read the first row's "Video link" hover-link.

If both fail → `{ "post_url": null, "error": "url_extraction_failed" }`.

## Dry-run

- Stop after step 7 (visibility set). Do not click Publish.
- Click "Cancel" / "Save as draft" to exit the wizard. YT keeps the upload as a private draft — the run is not "leaving residue" unexpectedly.
- `browser_close`.
- Return `{ "status": "dry_run_ok", "draft_residue": "yes — private draft saved in Studio" }` (call this out so dry-run cleanup is honest).

## Delete (called by `delete-youtube`)

Deletion in YT Studio is "move to trash"; the video stays for 30 days before final removal. The round-trip "verified-gone" check accepts a "Video unavailable" page rather than a hard 404.
