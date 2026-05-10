---
name: draft-threads
description: Draft a Threads post. 500-char native voice, conversational, minimal hashtags.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`, `theme`, `language`.
- `mode`: `post` | `video`.
- `local_image_path` or `local_video_path`: optional.
- `extra`: free-form, may include `reference`.

## Output (JSON)
```json
{
  "platform": "threads",
  "mode": "post|video",
  "caption": "...",
  "hashtags": ["#..."],
  "local_image_path": "/abs/... or null",
  "local_video_path": "/abs/... or null",
  "rationale": "..."
}
```

## Rules

1. Length: ≤ 500 chars. Threads has a softer character cap than X; you have room for a short story or a set-up + punch.
2. Hashtag count: respect `content_style.threads.hashtag_count` (default 1). Threads users dislike hashtag spam more than X / IG users.
3. Voice: conversational, low-formality. Threads tends toward "comment-section vibes" — a question or a take that invites replies works better than a polished press release.
4. Link policy = `inline` — Threads shows link previews; paste raw.
5. Threads identity = Instagram identity. Use the same handle and the same brand-voice cues as IG, but a different cadence (less polish, more chat).
6. No multi-post chains in this skill (single post only).

## Don'ts

- Do not call other skills.
- Do not paste tags from Instagram wholesale — Threads rewards fewer, more pointed tags.
- Do not hardcode brand strings.
