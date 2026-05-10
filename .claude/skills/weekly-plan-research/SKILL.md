---
name: weekly-plan-research
description: Per-platform top-post analysis of competitor products via fetch-reference (public).
---

> Common rules: `docs/OPERATING_RULES.md`. Subagent-friendly: orchestrator spawns one of these per platform in parallel.

## Input
- `platform`: one of `facebook|instagram|x|threads|youtube|tiktok`.
- `own_account_url`: from `socials.<platform>.url` in active brand YAML.
- `competitor_products`: list of `{ name, similar_to, socials.<platform> }` from `competitor_products[]` in brand YAML, filtered to entries where `socials.<platform>` is non-empty. De-duplicated by URL.
- `lookback_days`: integer (default 14) — used for own-post analysis filtering only.

## Output (JSON)

```json
{
  "platform": "instagram",
  "researched_at": "<ISO>",
  "topic_research_rows": [
    {
      "competitor_product": "ChargerLAB POWER-Z",
      "similar_to": "md-903",
      "relevant_to": "md-903",
      "post_url": "https://...",
      "posted_at": "<ISO>",
      "likes": 1234, "comments": 56, "shares": null, "views": null,
      "tone": "technical-demo",
      "layout": "video + caption",
      "hook": "first-line text",
      "why_it_resonated": "concise reason",
      "takeaway_for_us": "one-sentence insight applicable to our SKU"
    }
  ]
}
```

## Strategy

### Competitor products (no login)

1. De-duplicate `competitor_products[].socials[<platform>]` URLs (multiple entries may share the same handle).
2. For each unique URL, spawn a `fetch-reference` subagent — orchestrator handles the spawning. This skill receives back `summary` / `key_points` / `images` per page.
3. Identify up to 3 top posts per URL (by visible engagement; if hidden, by recency).
4. For each post:
   - Set `competitor_product` to the rival entry name (or join names with " / " if multiple entries share the URL).
   - Set `similar_to` to that entry's brand-level value (or join if multiple).
   - Determine `relevant_to` from the post content itself: which of our SKUs (`md-903 | md-905 | both | neither`) does the post topically map to? Use the post's text + media to decide; do not default to `similar_to`.
5. Fill `tone`, `layout`, `hook`, `why_it_resonated`, `takeaway_for_us`.

### LLM-extract notes per row

- `tone`: short phrase (e.g. "technical-demo", "high-energy hype", "mock-academic").
- `layout`: structure description (e.g. "TFT close-up + 2-line caption + 8 hashtags").
- `hook`: first 70 chars of the post that does the work.
- `why_it_resonated`: 1 sentence; tie to emotion / utility / timing / format novelty / community-specific reference.
- `takeaway_for_us`: 1 sentence applicable to one of our SKUs.

## Don'ts

- Do not write to disk — return JSON only. Orchestrator persists to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.
- Do not scrape competitor pages with the logged-in browser session.
- Do not invent engagement metrics. Missing → `null`.
- Do not exceed 8 topic_research_rows per platform — quality over volume.
- Do not call other skills directly. The orchestrator chains everything.
