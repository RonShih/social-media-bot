---
name: draft-youtube
description: Draft a YouTube video title + description + tags. SEO-leaning. Title is the traffic lever.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`, `theme`, `language`.
- `local_video_path`: caller-provided absolute path.
- `format`: `long` (regular video) | `short` (≤ 60s vertical).
- `extra`: free-form, may include `reference`.

## Output (JSON)
```json
{
  "platform": "youtube",
  "format": "long|short",
  "title": "≤ 100 chars, SEO-leaning, hook + keyword",
  "description": "first 150 chars are the SERP snippet — pack the value prop there",
  "tags": ["..."],
  "local_video_path": "/abs/...",
  "rationale": "..."
}
```

## Rules

1. Title: ≤ 100 chars. Front-load the keyword that matches search intent. No clickbait that the video does not deliver.
2. Description: first 150 chars are the search-snippet — make them stand alone. Add chapters / timestamps if `extra.chapters` is provided. Always include `storefronts.*` URLs at the bottom for product-related videos.
3. Tags: respect `content_style.youtube.hashtag_count` (default 8). Brand handle (`@<youtube.handle>`) appears in description, not tags.
4. Shorts: title ≤ 70 chars; description ≤ 200 chars; up to 3 `#shorts`-adjacent tags in the description (YouTube auto-detects short format).
5. Tone per `voice.tone`. Avoid `forbidden_words` / `forbidden_behavior`.

## Don'ts

- Do not duplicate keywords beyond search relevance ("PD PD PD" stuffing → demoted).
- Do not put hashtags in the title (YT prefers them in description).
- Do not call other skills.
- Do not hardcode brand strings.
