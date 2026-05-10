---
name: weekly-plan-draft
description: Generate caption + hashtags + media plan + product_id for one schedule slot. Subagent-friendly: orchestrator spawns one per slot in parallel.
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `slot`: one row from `weekly-plan-schedule.schedule[]` (slot_id, weekday, time_local, platform, mode, theme; `product_id` arrives as `null` and this skill fills it).
- `available_products`: full `products[]` from active brand YAML.
- `topic_research_rows`: subset of `topic_research_rows` filtered to this slot's platform.
- `own_history_rows`: subset of `own_history_rows` filtered to this slot's platform.
- `brand_yaml`: the active brand profile (full).
- `reference`: optional — `fetch-reference` output if the slot is news/event-driven.

## Output (JSON)

```json
{
  "slot_id": "2026-W19-ig-mon-1230",
  "platform": "instagram",
  "mode": "post",
  "product_id": "md-905",
  "caption": "...",
  "hashtags": ["#...", "#..."],
  "media_path": "media/assets/<brand>/<...>.jpg",
  "reference_urls": ["https://..."],
  "draft_id": "weekly-2026-W19-ig-mon-1230",
  "rationale": "one or two sentences on product/tone/hook choice grounded in research_rows"
}
```

`draft_id` is synthesized from `slot_id` so `/publish-from-plan` can write a normal draft JSON for tracing.

## Behavior

1. Load the matching `draft-<platform>` SKILL.md mentally — it sets the rules for length, hashtag count, link policy. Follow them.

2. **Pick `product_id`** from `available_products`:
   - For each product, score `slot.theme` against `product.suggested_themes` (substring or stem match counts). Pick the highest-scoring product.
   - If two products tie or `slot.theme` is generic, pick the product with fewer slots already assigned this week (alternation tie-break — orchestrator passes a `weekly_assignments_so_far` count if available; otherwise pick alphabetically).
   - If `available_products` is empty, set `product_id: null` and proceed.

3. **Filter research for SKU**:
   - From `topic_research_rows`, keep rows where `relevant_to == product_id` or `relevant_to == "both"`.
   - Use these + `own_history_rows` to abstract patterns (tone, opening hook style, layout) — do not lift sentences.

4. **Pick `media_path`**:
   - Look in `media/assets/<brand>/<product_id>/` for an image / video matching `mode`.
   - If nothing fits → fall back to `media/assets/<brand>/` library roots.
   - If still nothing → return `media_path: null` and add to `rationale` "needs media (orchestrator: route to image-generator)".

5. Honor `voice.forbidden_words` and `voice.forbidden_behavior` from the brand YAML.

## Don'ts

- Do not call `publish-*` or `image-generator` directly — the orchestrator does that on the back of `media_path: null`.
- Do not write files — return JSON only.
- Do not duplicate captions across slots — vary hooks even when the theme is identical.
- Do not invent engagement metrics or research data. Use what `topic_research_rows` / `own_history_rows` provide; if a slot's platform has no research data, draft conservatively from brand YAML alone and say so in `rationale`.
- Do not pick a `product_id` not present in `available_products`.
