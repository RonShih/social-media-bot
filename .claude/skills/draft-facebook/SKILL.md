---
name: draft-facebook
description: Draft a Facebook caption + hashtags. Medium length, link-friendly, low hashtag density.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `product_id`: matches `products[].id` in brand YAML.
- `theme`: from `content_themes`.
- `language`: `zh-TW` / `en` / `ja` / `de` (default: brand `primary_language`).
- `mode`: `post` (image post) | `video` (Reel). Caller sets.
- `local_image_path` or `local_video_path`: caller-provided absolute path. Existence is checked at publish time, not here.
- `extra`: free-form caller hints (promotion, season, key selling points, an injected `reference` from `fetch-reference`).

## Output (JSON)
```json
{
  "platform": "facebook",
  "mode": "post|video",
  "caption": "...",
  "hashtags": ["#NoirsBoxes", "#..."],
  "local_image_path": "/abs/...",
  "local_video_path": null,
  "rationale": "one or two sentences explaining the choices"
}
```

## Rules

1. Length: caption ≤ 500 chars (incl. line breaks). FB readers tolerate full stories — do not over-truncate.
2. Structure: hook (1 line) → story / selling points (2-4 lines) → CTA + link (`storefronts.amazon|taobao|rakuten` or brand `company.website`).
3. Hashtags: 3–6 tags, follow `content_style.facebook.hashtag_count`. Brand tag (e.g. `#<display_name no spaces>`) is mandatory.
4. Tone: per `voice.tone`; avoid all `voice.forbidden_words` and `voice.forbidden_behavior`.
5. Links: paste raw — FB auto-renders OG card.
6. Do not promise delivery dates / discounts unless `extra.promotion` says otherwise.
7. If `extra.reference` is present, fold its `summary` / `key_points` into the body. Cite the source URL only if it strengthens the post; otherwise drop it.

## Don'ts

- Do not call other skills.
- Do not open Playwright / browser.
- Do not change `local_image_path` / `local_video_path` — return what the caller passed.
- Do not hardcode brand strings — read from YAML.
