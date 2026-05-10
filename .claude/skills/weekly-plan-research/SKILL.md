---
name: weekly-plan-research
description: Per-platform top-post analysis. Own posts via Playwright (logged in, real metrics). Competitors via fetch-reference (public WebFetch only).
---

> Common rules: `docs/OPERATING_RULES.md`. Subagent-friendly: orchestrator spawns one of these per platform in parallel.

## Input
- `platform`: one of `facebook|instagram|x|threads|youtube|tiktok`.
- `own_account_url`: from `socials.<platform>.url` in active brand YAML.
- `competitor_urls`: list from `competitors[]` and `reference_urls.competitors[]` in brand YAML (may be empty).
- `lookback_days`: integer (default 14).

## Output (JSON)

```json
{
  "platform": "instagram",
  "researched_at": "<ISO>",
  "rows": [
    {
      "source": "own | competitor",
      "account": "@handle",
      "post_url": "https://...",
      "post_type": "image | reel | video | text",
      "likes": 1234,
      "comments": 56,
      "shares": null,
      "tone": "warm-conversational",
      "layout": "1-line hook + body + 8 hashtags",
      "hook": "first-line text",
      "why_it_resonated": "concise reason — emotion / utility / timing / format"
    }
  ]
}
```

## Strategy

### Own posts (real metrics)

- Use Playwright with the brand's logged-in session (the orchestrator wraps in action log).
- Navigate to `own_account_url`. Read the top N posts in the last `lookback_days`. For each, capture: post_url, post_type, likes, comments. (Shares/saves where the platform exposes them.)
- Sort by an engagement proxy: `likes + 3*comments + 2*shares` (saves are platform-specific; weight at 3 if available).
- Take the top 5.

### Competitor posts (no login)

- For each `competitor_urls`, spawn a `fetch-reference` subagent — orchestrator handles the spawning. This skill receives back `summary` / `key_points` / `images`.
- Public engagement counts are platform-dependent; record what's visible on the public page (often hidden for X without login). When metrics are not visible, set the metric fields to `null` and lean on `tone` / `layout` / `hook` analysis.
- Take up to 3 competitor entries per platform.

### LLM-extract per row

After capturing the raw fields, the LLM fills in:

- `tone`: one short phrase (e.g. "warm-conversational", "high-energy hype", "mock-academic").
- `layout`: structure description (e.g. "hook + 3-bullet body + tag block").
- `hook`: first 70 chars of the post that does the work.
- `why_it_resonated`: 1-sentence reason. Tie it to one of: emotion, utility, timing, format novelty, community-specific reference.

## Don'ts

- Do not write to disk — return JSON only. The orchestrator persists it under `reports/plans/<brand>/<iso_week>/research/<platform>.json`.
- Do not scrape competitor pages with the logged-in browser session (TOS gray zone). Competitors go through `fetch-reference` only.
- Do not invent engagement metrics. Missing → `null`.
- Do not call other skills directly. The orchestrator chains `fetch-reference` calls.
- Do not exceed 8 rows per platform — quality over volume.
