---
name: image-generator
description: Pick from the brand asset library or generate a new image for a post. Returns a relative path under media/assets/<brand>/.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand: `config/brands/<active>.yaml`.

## Input
- `caption`: post text (used to inform the prompt or the library pick).
- `product_id`: matches `products[].id` in brand YAML. Library lookup happens in `media/assets/<brand>/<product_id>/`.
- `platform`: drives aspect ratio. `facebook|instagram` → 1:1, `instagram_story|tiktok` → 9:16, `youtube` → 16:9, `x|threads` → 1:1 or 16:9.

## Output
```json
{ "image_path": "media/assets/<brand>/<...>.jpg", "source": "library|generated" }
```

`image_path` is relative to repo root.

## Steps

1. `ls media/assets/<brand>/<product_id>/` (and `media/assets/<brand>/<brand.media_library.hints>` directories) to enumerate existing assets.
2. If at least one asset is suitable for the caption + platform aspect ratio → return `{ source: "library" }` with that path. Prefer images not used in the last 14 days (check `data/stats-history/<brand>.json` `Schedule.media_path` history if available).
3. Otherwise generate:
   - LLM-summarize the caption + brand `media_library.hints` into an English image prompt (favor on-brand visuals; respect `voice.forbidden_behavior`).
   - Call the image API (default OpenAI Images via `OPENAI_API_KEY`; caller-provided otherwise).
   - Save under `media/assets/<brand>/<product_id>/generated/<YYYYMMDD-HHMM>.jpg` via `local-writer`.
   - Return that relative path with `source: "generated"`.

## Don'ts

- Do not upload to Drive / cloud — everything stays under `media/assets/`.
- Do not embed competitor logos or recognizable faces.
- Do not reuse images used in the last 14 days (cross-check `Schedule.media_path` if a recent plan exists).
- Do not call other skills except `local-writer` for the save step.

## Naming conventions

- Product photos: `<product_id>.jpg`, `<product_id>-<variant>.jpg`.
- Generated: `<product_id>/generated/<YYYYMMDD-HHMM>.jpg`.
- Short videos: `<product_id>-short-<slug>.mp4`.
