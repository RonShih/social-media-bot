---
description: Generate (or regenerate) this week's weekly plan. Spawns research subagents per platform in parallel; emits plan.json + plan.xlsx.
argument-hint: "[--week <YYYY-Www>] [--dry]   # default: current ISO week"
---

End-to-end weekly-plan generation. Subagents in parallel for research + drafting. Main session for the metrics-scrape step (uses Playwright on own posts) and the xlsx export.

**Per-step confirmation gates.** After steps 5, 6, 7, and 8, pause and reply a preview to the user. Wait for `ok|go|continue` before proceeding. Anything else = treat as feedback, adjust or abort, do not advance. Channel-aware: TG channel uses `reply` tool; terminal uses main-session text. Gate replies are plain text, no markdown.

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
   - **`browser_close` when done — required before the gate / step 6.**

   **🚦 Gate 1 — last-week metrics**

   Reply preview (skip this gate entirely if step 5 was a no-op):

   ```
   📊 last week (<prev iso_week>) metrics
   facebook: 3 posts · avg 142 likes · top "<caption excerpt>" 380 likes
   instagram: 4 posts · avg 89 likes · top "<...>" 220 likes
   ...

   updated: reports/plans/<brand>/<prev iso_week>/plan.json (Metrics)
   reply `ok` to continue with research, or send feedback.
   ```

   Wait for `ok`. Any other reply = pause, discuss, do not advance.

6. **Research per platform** — branch by platform (per `weekly-plan-research/SKILL.md` Mode A vs Mode B).

   **Mode A — public-page platforms (FB, X, YT)**: subagents in parallel.
   - For each Mode-A platform spawn `subagent_type: general-purpose`:
     - Prompt: "Read `.claude/skills/weekly-plan-research/SKILL.md`. Run **Mode A**. Inputs: `competitor_products` filtered to entries with `socials.<p>` non-empty (de-duplicated by URL); spawn `fetch-reference` subagents per unique competitor URL. Return JSON exactly per SKILL.md output."

   **Mode B — login-walled platforms (IG, TikTok, Threads)**: main-session sequential. Subagents cannot reach Playwright MCP.
   - For each Mode-B platform with non-empty competitor URLs:
     - Main session runs the SKILL.md Mode B steps (navigate profile → extract top-3 post URLs → navigate each → extract `og:description`). Wrap every MCP call in the action log.
     - `mcp__playwright__browser_close` after the platform's URLs are done (release profile lock before next platform / next step).
   - Skip platforms with zero competitor URLs in YAML (write an empty research file with `topic_research_rows: []` + `note` for downstream drafts).
   - Persist each platform's research to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.

   **🚦 Gate 2 — competitor research**

   Reply preview:

   ```
   🔍 competitor research <iso_week>
   facebook: 8 competitor posts · themes: <theme1>, <theme2>, <theme3>
   instagram: 6 posts · themes: <...>
   threads: 4 posts · themes: <...>
   x: 5 posts · themes: <...>
   youtube: 3 posts · themes: <...>
   tiktok: 7 posts · themes: <...>

   files: reports/plans/<brand>/<iso_week>/research/*.json
   reply `ok` to continue with schedule, or send feedback.
   ```

   Wait for `ok`.

7. **Schedule** (main session, no subagent — pure compute):
   - Read `.claude/skills/weekly-plan-schedule/SKILL.md`.
   - Inputs: aggregated research, `prev_metrics` (if step 5 ran), brand `content_style`.
   - Output: `frequency[]` + `schedule[]` (each `slot.product_id = null`).

   **🚦 Gate 3 — schedule**

   Reply preview:

   ```
   🗓 schedule <iso_week> · 22 slots across 6 platforms
   facebook (3): Tue 11:00 / Thu 19:00 / Sat 11:00
   instagram (4): Mon 12:30 / Wed 20:00 / Fri 12:30 / Sun 20:00
   threads (3): ...
   x (5): ...
   youtube (1): Sat 18:00
   tiktok (6): ...

   reply `ok` to continue with drafts, or send feedback (e.g. "FB +1 slot Sun 19:00", "drop YT this week").
   ```

   Wait for `ok`.

8. **Drafts** (subagents, parallel — one per slot):
   - For each `slot` in `schedule[]`, spawn one `weekly-plan-draft` subagent.
   - Pass: `slot`, `available_products` (full `brand.products[]`), `topic_research_rows` filtered to that platform, `brand_yaml`, `reference` (if applicable).
   - Subagent prompt: "Read `.claude/skills/weekly-plan-draft/SKILL.md`. Pick product_id by theme fit. Return JSON exactly per output schema."
   - Aggregate all draft results back into `schedule[]` rows (caption, hashtags, media_path, reference_urls, draft_id, rationale, product_id).

   **🚦 Gate 4 — drafts**

   Reply preview (one line per slot, caption truncated to ~80 chars):

   ```
   ✍️ drafts <iso_week>
   FB Tue 11:00 [<product>] "<caption excerpt...>" #tag1 #tag2 → media/assets/.../x.jpg
   IG Mon 12:30 [<product>] "<...>" → ...
   TH Wed 09:00 [<product>] "<...>"
   X  Mon 08:00 [<product>] "<...>"
   YT Sat 18:00 [<product>] "<...>" → media/assets/.../y.mp4
   TT Fri 19:00 [<product>] "<...>" → ...
   ... (all 22 slots)

   reply `ok` to compose plan.json + xlsx, or send feedback per slot
   (e.g. "redo FB Tue", "swap product on IG Mon", "shorten X captions").
   ```

   Wait for `ok`.

9. **Compose `plan.json`**:

    ```json
    {
      "schedule": [...],
      "frequency": [...],
      "topic_research": [...],
      "metrics": [],
      "meta": {
        "brand": "<slug>",
        "iso_week": "<YYYY-Www>",
        "generated_at": "<ISO>",
        "prev_week_plan_path": "<path or null>",
        "model": "claude-opus-4-7",
        "notes": ""
      }
    }
    ```

    Write to `reports/plans/<brand>/<iso_week>/plan.json`.

10. **Export xlsx**: invoke `weekly-plan-export` with the json path. Verify file exists.

11. **Reply** (channel: TG `reply`; terminal: main-session text). Plain text:

    ```
    📅 weekly plan <iso_week>
    schedule: 22 slots across 6 platforms
    facebook: 3 posts (Tue Thu Sat 11:00 / 19:00)
    instagram: 4 posts (Mon Wed Fri Sun 12:30 / 20:00)
    ...

    plan.json: reports/plans/<brand>/<iso_week>/plan.json
    plan.xlsx: reports/plans/<brand>/<iso_week>/<iso_week>-MMDD-MMDD.xlsx

    last week's metrics: <updated | none>

    review the plan, then run /publish-from-plan --day today.
    ```

## Verification

- [ ] `reports/plans/<brand>/<iso_week>/plan.json` and the matching `.xlsx` exist.
- [ ] `Schedule` has at least one slot per requested platform; every slot has a non-null `product_id` (when `brand.products[]` is non-empty).
- [ ] `TopicResearch` has rows for at least the platforms with reachable competitor accounts (FB, X for v1).
- [ ] If a previous-week plan existed, its `Metrics` sheet has fresh rows.
- [ ] Action log written for MCP review step.
- [ ] All 4 gates (or 3 if no prev-week metrics) were sent and acknowledged before final compose.

## Don'ts

- Do not run own-post Playwright scraping in a subagent — the browser session does not propagate. Run in main session sequentially.
- Do not run Mode-B competitor scraping in a subagent — same reason. Main session only.
- Do not perform engagement actions on competitor pages during Mode-B scraping — read-only navigation + `og:description` extract only (no like / comment / share / follow / story view).
- Do not exceed 3 posts per competitor URL in Mode B (per `weekly-plan-research/SKILL.md`).
- Do not generate captions in the main session — always spawn `weekly-plan-draft` subagents.
- Do not skip the xlsx export. The user reads xlsx, not JSON.
- Do not modify last-week plans except via `weekly-plan-review` (Metrics sheet only).
