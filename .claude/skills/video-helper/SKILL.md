---
name: video-helper
description: Probe a video file (duration, aspect ratio, codec) via ffprobe. Used by publish-* video flows for sanity checks.
---

> Common rules: `docs/OPERATING_RULES.md`. No transcoding, no editing — pure inspection (and one optional simple trim).

## probe

Input: `path` (absolute or relative to repo root).

Run:

```bash
ffprobe -v error -print_format json -show_format -show_streams "<abs path>"
```

Parse to:

```json
{
  "abs_path": "...",
  "duration_sec": 27.5,
  "width": 1080,
  "height": 1920,
  "aspect_ratio": "9:16",
  "codec": "h264",
  "audio_codec": "aac",
  "size_bytes": 12345678
}
```

`aspect_ratio` is reduced (e.g. `1080x1920` → `9:16`). If width / height does not reduce to a clean integer ratio, return the decimal (`1.78`).

## platform-fit check

Input: `probe` (output above) + `platform`.

Return:

```json
{
  "platform": "tiktok",
  "fits": true,
  "warnings": ["..."]
}
```

Rules:

- TikTok / Instagram Reel / YouTube Short: prefer 9:16, duration ≤ 60s. Aspect drift up to ±0.05 is OK; durations over 60s warn (Shorts truncate).
- YouTube long: 16:9 preferred. No duration limit (channel-dependent).
- Facebook video / X video / Threads video: 1:1, 4:5, 16:9, or 9:16 all acceptable. Warn on extreme aspect (e.g. 21:9).
- Codec must be `h264` (or `hevc` for newer YT). Unknown codec → warn.

`fits: false` only when the file is structurally incompatible (e.g. uploaded `.mp3` audio masquerading as video). Aspect-ratio mismatch → `fits: true, warnings: [...]`. Caller (publish-*) can still proceed; it's the caller's call.

## simple-trim (optional)

Input: `path`, `start_sec`, `end_sec`. Returns trimmed file under `media/assets/<brand>/<orig name>-trim-<start>-<end>.mp4`.

```bash
ffmpeg -y -i "<abs path>" -ss <start> -to <end> -c copy "<out path>"
```

Stream-copy only (`-c copy`). No transcoding. Output format must remain mp4.

## Don'ts

- Do not transcode — if a stream-copy trim fails, return `{ "error": "trim_requires_transcode" }` rather than fall back to `-c:v libx264`.
- Do not call `publish-*`, `local-writer`, or other skills.
- Do not write probe results to disk — return JSON only.
- Do not assume `ffprobe` / `ffmpeg` are installed — if missing, return `{ "error": "ffprobe not installed" }` and let the caller decide.
