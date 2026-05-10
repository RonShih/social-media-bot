---
description: Generate (or regenerate) this week's weekly plan. Spawns research subagents per platform in parallel; emits plan.json + plan.xlsx.
argument-hint: "[--week <YYYY-Www>] [--dry]   # default: current ISO week"
---

End-to-end weekly-plan generation. Subagents in parallel for research + drafting. Main session for the metrics-scrape step (uses Playwright on own posts) and the xlsx export.

## Steps

1. Resolve target ISO week:
   - `--week 2026-W19` → use it.
   - Default → current ISO week (`date +%G-W%V`).
2. Resolve active brand (`BRAND` env → `config/active-brand`).
3. Make `reports/plans/<brand>/<iso_week>/research/` if missing.
4. Generate run id (`YYYYMMDD-HHMMSS-<rand4>`); set `meta.mode = "weekly-plan"`.

5. **Last-week metrics (MCP)** — only if a previous plan exists at `reports/plans/<brand>/<prev iso_week>/plan.json` with at least one `Schedule.posted_url`:
   - Read `.claude/skills/weekly-plan-review/SKILL.md`.
   - Main session runs the Playwright MCP scrape (logged-in, own posts only). Wrap each MCP call in the action log.
   - Updates `prev plan.json` (Metrics sheet) and `data/stats-history/<brand>.json`.
   - Re-exports the previous week's xlsx via `weekly-plan-export`.
   - **`browser_close` when done — required before step 6.**

6. **Own-top scrape (script, sequential)**:
   - For each platform in `socials[]`:
     - Run: `node scripts/scrape-top-posts.mjs --brand <slug> --platform <p> --account-url <socials.p.url> --recent 60 --top 10 --out reports/plans/<brand>/<iso_week>/research/own-<p>-top.json --run-id <run_id>`.
     - On non-zero exit, the script writes a structured error JSON to the `--out` path. Capture it; surface to the user but continue with other platforms.
   - All scrape calls are sequential (single chromium, shared profile).

7. **Research per platform** (subagents, parallel — one per platform):
   - For each platform spawn `subagent_type: general-purpose`:
     - Prompt: "Read `.claude/skills/weekly-plan-research/SKILL.md`. Inputs: `own_top_json_path = reports/plans/<brand>/<iso_week>/research/own-<p>-top.json`; `competitor_products` filtered to entries with `socials.<p>` non-empty (de-duplicated by URL); spawn `fetch-reference` subagents per unique competitor URL. Return JSON exactly per SKILL.md output."
   - Persist each platform's research to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.

8. **Schedule** (main session, no subagent — pure compute):
   - Read `.claude/skills/weekly-plan-schedule/SKILL.md`.
   - Inputs: aggregated research, `prev_metrics` (if step 5 ran), brand `content_style`.
   - Output: `frequency[]` + `schedule[]` (each `slot.product_id = null`).

9. **Drafts** (subagents, parallel — one per slot):
   - For each `slot` in `schedule[]`, spawn one `weekly-plan-draft` subagent.
   - Pass: `slot`, `available_products` (full `brand.products[]`), `topic_research_rows` filtered to that platform, `own_history_rows` filtered to that platform, `brand_yaml`, `reference` (if applicable).
   - Subagent prompt: "Read `.claude/skills/weekly-plan-draft/SKILL.md`. Pick product_id by theme fit. Return JSON exactly per output schema."
   - Aggregate all draft results back into `schedule[]` rows (caption, hashtags, media_path, reference_urls, draft_id, rationale, product_id).

10. **Compose `plan.json`**:

    ```json
    {
      "schedule": [...],
      "frequency": [...],
      "topic_research": [...],
      "own_history": [...],
      "metrics": [],
      "meta": {
        "brand": "<slug>",
        "iso_week": "<YYYY-Www>",
        "generated_at": "<ISO>",
        "prev_week_plan_path": "<path or null>",
        "own_top_scraped_at": "<ISO>",
        "model": "claude-opus-4-7",
        "notes": ""
      }
    }
    ```

    Write to `reports/plans/<brand>/<iso_week>/plan.json`.

11. **Export xlsx**: invoke `weekly-plan-export` with the json path. Verify file exists.

12. **Reply** (channel: TG `reply`; terminal: main-session text). Plain text:

    ```
    📅 weekly plan <iso_week>
    schedule: 22 slots across 6 platforms
    facebook: 3 posts (Tue Thu Sat 11:00 / 19:00)
    instagram: 4 posts (Mon Wed Fri Sun 12:30 / 20:00)
    ...

    plan.json: reports/plans/<brand>/<iso_week>/plan.json
    plan.xlsx: reports/plans/<brand>/<iso_week>/<iso_week>-MMDD-MMDD.xlsx

    own-top scraped: 6/6 platforms
    last week's metrics: <updated | none>

    review the plan, then run /publish-from-plan --day today.
    ```

## Verification

- [ ] `reports/plans/<brand>/<iso_week>/plan.json` and the matching `.xlsx` exist.
- [ ] `Schedule` has at least one slot per requested platform; every slot has a non-null `product_id` (when `brand.products[]` is non-empty).
- [ ] `OwnHistory` has rows for at least one platform (script ran successfully).
- [ ] `TopicResearch` has rows for at least the platforms with reachable competitor accounts (FB, X for v1).
- [ ] If a previous-week plan existed, its `Metrics` sheet has fresh rows.
- [ ] Action log written for MCP review step. Scrape logs written for each own-top scrape under `data/scrape-logs/`.

## Don'ts

- Do not run own-post Playwright scraping in a subagent — the browser session does not propagate. Run in main session sequentially.
- Do not scrape competitor pages with the logged-in session.
- Do not generate captions in the main session — always spawn `weekly-plan-draft` subagents.
- Do not skip the xlsx export. The user reads xlsx, not JSON.
- Do not modify last-week plans except via `weekly-plan-review` (Metrics sheet only).
