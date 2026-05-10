---
name: draft-instagram
description: Draft an Instagram Feed caption + hashtags. Visual-first, dense hashtags, the first line decides scroll-stop.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`, `theme`, `language`: as in `draft-facebook`.
- `mode`: `post` (Feed photo) | `video` (Reel).
- `local_image_path` or `local_video_path`: caller-provided.
- `extra`: free-form, may include `reference` from `fetch-reference`.

## Output (JSON)
```json
{
  "platform": "instagram",
  "mode": "post|video",
  "caption": "...",
  "hashtags": ["#...", "#..."],
  "local_image_path": "/abs/...",
  "local_video_path": null,
  "rationale": "..."
}
```

## Rules

1. First line wins. The opening line must hook on its own without context — IG truncates after ~1 line in the feed.
2. Length: respect `content_style.instagram.caption_length` (default `medium`).
3. Hashtags: respect `content_style.instagram.hashtag_count` (default 8). Mix tag volumes — 1 brand, 2-3 niche, 2-3 mid, 1-2 mass.
4. Place the hashtag block on its own paragraph after a blank line (or after `.\n.\n.\n` separator) — see `content_style.instagram.notes`.
5. Tone per `voice.tone`. Avoid `forbidden_words` / `forbidden_behavior`.
6. Link policy = `bio_only` by default — never paste raw URLs in the caption (IG kills them visually). Reference "link in bio" if a CTA is needed.
7. If `extra.reference` is present, draw on `summary` / `key_points` for the body, but keep IG voice — concise and visual.

## Don'ts

- Do not call other skills.
- Do not open Playwright / browser.
- Do not paste URLs (use "link in bio").
- Do not hardcode brand strings — read from YAML.
