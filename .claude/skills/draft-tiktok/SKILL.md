---
name: draft-tiktok
description: Draft a TikTok caption + hashtags. First 3 seconds hook lives in the video; caption is short with trend-aware tags.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`, `theme`, `language`.
- `local_video_path`: caller-provided absolute path.
- `extra`: free-form, may include `reference`, `trends` (current sound / hashtag trends).

## Output (JSON)
```json
{
  "platform": "tiktok",
  "caption": "...",
  "hashtags": ["#fyp", "#..."],
  "local_video_path": "/abs/...",
  "rationale": "..."
}
```

## Rules

1. Caption: ≤ 150 chars. TikTok captions don't carry the load — the video does. Use the caption to signpost the hook or pose a question.
2. Hashtags: respect `content_style.tiktok.hashtag_count` (default 5). Mix:
   - 1 brand tag.
   - 1-2 niche / community tags relevant to the brand.
   - 1-2 trend-aware tags (use `extra.trends` if caller provided).
3. CTA: short, e.g. "link in bio" / "shop in bio". `link_policy: bio_only` by default.
4. Tone per `voice.tone`. Avoid `forbidden_words` / `forbidden_behavior`.
5. Trends fade fast — if `extra.trends` is missing, fall back to evergreen tags like `#fyp` + niche tags. Do not invent trend names.

## Don'ts

- Do not paste URLs in the caption (`bio_only` policy).
- Do not call other skills.
- Do not hardcode brand strings.
