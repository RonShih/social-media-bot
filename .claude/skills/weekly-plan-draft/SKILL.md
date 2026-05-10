---
name: weekly-plan-draft
description: Generate caption + hashtags + media plan for one schedule slot. Subagent-friendly: orchestrator spawns one per slot in parallel.
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `slot`: one row from `weekly-plan-schedule.schedule[]` (slot_id, weekday, time_local, platform, mode, theme, product_id).
- `research_rows`: subset of the research output filtered to this slot's platform. The LLM should learn *tone, layout, hook* patterns from these — not copy verbatim.
- `brand_yaml`: the active brand profile (full).
- `reference`: optional — `fetch-reference` output if the slot is news/event-driven.

## Output (JSON)

```json
{
  "slot_id": "2026-W19-ig-mon-1230",
  "platform": "instagram",
  "mode": "post",
  "caption": "...",
  "hashtags": ["#...", "#..."],
  "media_path": "media/assets/<brand>/<...>.jpg",
  "reference_urls": ["https://..."],
  "draft_id": "weekly-2026-W19-ig-mon-1230",
  "rationale": "one or two sentences on tone/hook choice grounded in research_rows"
}
```

`draft_id` is synthesized from `slot_id` so `/publish-from-plan` can write a normal draft JSON for tracing.

## Behavior

1. Load the matching `draft-<platform>` SKILL.md mentally — it sets the rules for length, hashtag count, link policy. Follow them.
2. From `research_rows`, abstract the patterns (tone, opening hook style, layout) — do not lift sentences.
3. Pick `media_path`:
   - If `slot.product_id` is set → look in `media/assets/<brand>/<product_id>/` for an image / video matching `mode`.
   - If nothing fits → fall back to `media/assets/<brand>/` library roots.
   - If still nothing → return `media_path: null` and add to `rationale` "needs media (orchestrator: route to image-generator)".
4. Honor `voice.forbidden_words` and `voice.forbidden_behavior` from the brand YAML.

## Don'ts

- Do not call `publish-*` or `image-generator` directly — the orchestrator does that on the back of `media_path: null`.
- Do not write files — return JSON only.
- Do not duplicate captions across slots — vary hooks even when the theme is identical.
- Do not invent engagement metrics or research data. Use what `research_rows` provides; if a slot's platform has no research data, draft conservatively from brand YAML alone and say so in `rationale`.
