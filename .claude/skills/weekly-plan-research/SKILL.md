---
name: weekly-plan-research
description: Per-platform top-post analysis. Own posts via Node Playwright script (logged in, real metrics). Competitor products via fetch-reference (public).
---

> Common rules: `docs/OPERATING_RULES.md`. Subagent-friendly: orchestrator spawns one of these per platform in parallel, **but** the own-post scrape step happens in the main session before subagents fan out (see Strategy below).

## Input
- `platform`: one of `facebook|instagram|x|threads|youtube|tiktok`.
- `own_account_url`: from `socials.<platform>.url` in active brand YAML.
- `own_top_json_path`: absolute path to the JSON written by `scripts/scrape-top-posts.mjs` (main session produces this before spawning the subagent).
- `competitor_products`: list of `{ name, similar_to, socials.<platform> }` from `competitor_products[]` in brand YAML, filtered to entries where `socials.<platform>` is non-empty. De-duplicated by URL.
- `lookback_days`: integer (default 14) — used for own-post analysis filtering only.

## Output (JSON)

```json
{
  "platform": "instagram",
  "researched_at": "<ISO>",
  "own_history_rows": [
    {
      "post_url": "https://...",
      "posted_at": "<ISO>",
      "media_type": "image|reel|video",
      "likes": 1234, "comments": 56, "shares": null, "views": null,
      "caption_excerpt": "first 120 chars",
      "tone": "technical-demo",
      "layout": "TFT close-up + 2-line caption + 8 hashtags",
      "hook": "first-line text",
      "why_it_resonated": "concise reason",
      "repeatable_pattern": "lead with the on-screen number"
    }
  ],
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

### Own posts (script-produced, then LLM-analyzed)

The orchestrator runs `node scripts/scrape-top-posts.mjs --platform <p> --account-url <own_account_url> --top 10 --recent 60 --out <path>` in the **main session** (browser session does not propagate to subagents). It then passes the resulting JSON path to this skill running in a subagent.

In the subagent:
1. Load the JSON from `own_top_json_path`.
2. For each entry in `top[]`, fill in `tone`, `layout`, `hook`, `why_it_resonated`, `repeatable_pattern` using the `caption` and visible metrics. Truncate caption to 120 chars for `caption_excerpt`.
3. Drop entries posted before `now - lookback_days` if filtering is requested; otherwise pass through as-is.

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
- `takeaway_for_us`: 1 sentence applicable to one of our SKUs. (Topic rows only.)
- `repeatable_pattern`: 1 sentence describing the pattern we could replicate. (Own rows only.)

## Don'ts

- Do not write to disk — return JSON only. Orchestrator persists to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.
- Do not scrape competitor pages with the logged-in browser session.
- Do not scrape own pages with `fetch-reference` — own pages always come through the script.
- Do not invent engagement metrics. Missing → `null`.
- Do not exceed 10 own_history_rows or 8 topic_research_rows per platform — quality over volume.
- Do not call other skills directly. The orchestrator chains everything.
