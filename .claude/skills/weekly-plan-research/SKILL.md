---
name: weekly-plan-research
description: Per-platform top-post analysis of competitor products via fetch-reference (public).
---

> Common rules: `docs/OPERATING_RULES.md`. Two execution modes — orchestrator picks per platform:
> - **Public-page platforms (FB, X, YT)** → subagent + WebSearch / fetch-reference; parallel across platforms.
> - **Login-walled platforms (IG, TikTok, Threads)** → main session + Playwright MCP, read-only; sequential.
> Same input / output contract for both modes. See `## Strategy` below.

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

Pick mode by platform.

### Mode A — Public-page platforms (FB, X, YT)

Subagent execution. WebSearch / fetch-reference path.

1. De-duplicate `competitor_products[].socials[<platform>]` URLs (multiple entries may share the same handle).
2. For each unique URL, spawn a `fetch-reference` subagent — orchestrator handles the spawning. This skill receives back `summary` / `key_points` / `images` per page.
3. Identify up to 3 top posts per URL (by visible engagement; if hidden, by recency).
4. For each post:
   - Set `competitor_product` to the rival entry name (or join names with " / " if multiple entries share the URL).
   - Set `similar_to` to that entry's brand-level value (or join if multiple).
   - Determine `relevant_to` from the post content itself: which of our SKUs (`md-903 | md-905 | both | neither`) does the post topically map to? Use the post's text + media to decide; do not default to `similar_to`.
5. Fill `tone`, `layout`, `hook`, `why_it_resonated`, `takeaway_for_us`.

### Mode B — Login-walled platforms (IG, TikTok, Threads)

Main-session execution only — subagents cannot reach Playwright MCP. Sequential per URL.

For each unique competitor URL:

1. `mcp__playwright__browser_navigate` to the profile URL.
2. `mcp__playwright__browser_evaluate` to grab the first 3 post / reel anchor `href`s from the grid:
   ```js
   () => [...new Set([...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
            .map(a => a.href).filter(h => h.includes('/<handle>/')))]
       .slice(0, 3)
   ```
3. For each of the 3 post URLs:
   - `mcp__playwright__browser_navigate`
   - `mcp__playwright__browser_evaluate`:
     ```js
     () => ({
       og: document.querySelector('meta[property="og:description"]')?.content,
       time: document.querySelector('time[datetime]')?.getAttribute('datetime')
     })
     ```
   - `og.content` is shaped: `"<likes> likes, <comments> comments - <handle> on <date>: \"<caption verbatim>\". "`. Parse it.
   - Build a `topic_research_rows[]` entry per the schema. `views` and `shares` are not in `og:description` → leave `null`.
4. After all URLs done → `mcp__playwright__browser_close` (releases profile lock per OPERATING_RULES §9).

**Mode B constraints (enforced):**

- ≤ 3 posts per competitor URL per run.
- Read-only: navigation + `og:description` extract only. NEVER `like` / `comment` / `share`. Do NOT click story rings (story view exposes the brand account to the competitor).
- Every MCP call action-logged by the orchestrator (per OPERATING_RULES §10).
- If a profile returns 404 / "Page not found" → record the status, continue to next URL, surface in orchestrator-level Gate 2 reply for brand-safety review.

Why this works without contamination: `og:description` is server-rendered for the OG protocol (link-preview crawlers). Login state does not change what `og:description` returns; it only changes whether the SPA-rendered comment thread / engagement UI loads (which we do not need).

### LLM-extract notes per row

- `tone`: short phrase (e.g. "technical-demo", "high-energy hype", "mock-academic").
- `layout`: structure description (e.g. "TFT close-up + 2-line caption + 8 hashtags").
- `hook`: first 70 chars of the post that does the work.
- `why_it_resonated`: 1 sentence; tie to emotion / utility / timing / format novelty / community-specific reference.
- `takeaway_for_us`: 1 sentence applicable to one of our SKUs.

## Don'ts

- Do not write to disk — return JSON only. Orchestrator persists to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.
- Do not perform engagement actions on competitor pages — read-only navigation + `og:description` extract only. NEVER like / comment / share / follow / open stories.
- Do not invent engagement metrics. Missing → `null`.
- Do not exceed 8 topic_research_rows per platform — quality over volume.
- Do not exceed 3 posts per competitor URL in Mode B (small footprint, recency-first).
- Do not run Mode B from a subagent — browser session does not propagate. Mode B is main-session-only.
- Do not call other skills directly. The orchestrator chains everything.
