---
name: draft-x
description: Draft a single X (Twitter) post. 280-char hard cap including hashtags. Hook is everything.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`, `theme`, `language`.
- `mode`: `post` (text + optional image) | `video`.
- `local_image_path` or `local_video_path`: optional (caller-provided).
- `extra`: free-form, may include `reference`.

## Output (JSON)
```json
{
  "platform": "x",
  "mode": "post|video",
  "caption": "...",
  "hashtags": ["#..."],
  "local_image_path": "/abs/... or null",
  "local_video_path": "/abs/... or null",
  "rationale": "..."
}
```

## Rules

1. Total length ≤ 280 chars (caption + hashtags + spaces). Stop counting on the 280th char.
2. Hashtag count: respect `content_style.x.hashtag_count` (default 2). Quality over quantity — pick tags that route to active conversations.
3. Hook in the first 70 chars — that's what shows in expanded card / notification.
4. Link policy = `inline` by default — paste 1 short URL when relevant; X compresses it visually.
5. No emoji-stuffing (≤ 2 per post).
6. Avoid threads unless `extra.thread = true` is passed (this skill drafts a single post).
7. Tone per `voice.tone`. Avoid `forbidden_words` / `forbidden_behavior`.

## Don'ts

- Do not exceed 280 chars under any condition. If you cannot fit the message, return `{ "error": "cannot fit caption + hashtags in 280 chars", "rationale": "..." }`.
- Do not call other skills.
- Do not hardcode brand strings.
