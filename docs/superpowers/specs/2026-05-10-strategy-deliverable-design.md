# Strategy & Analysis Deliverable — Design

Date: 2026-05-10
Brand: noirs-boxes
Owner: Ron
Status: Draft, awaiting user approval

## 1. Goal

Make `/weekly-plan` produce a single human-readable deliverable
(`plan.xlsx`, 6 sheets) that covers all 5 strategy & analysis needs the user
listed:

1. Per-platform competitor top-post analysis (tone / layout / hook / why it
   resonated).
2. Per-platform best posting frequency + time slots.
3. Last week's posted-URL metrics (re-scraped).
4. NoirsBoxes own historical top posts per platform (LLM analysis on top of
   raw scrape).
5. Drafts + schedule for the upcoming week, with each slot bound to a real
   product (MD-903 or MD-905) by theme fit.

The existing `/weekly-plan` command + `weekly-plan-*` skills cover most of
this. The gaps are:

- Brand YAML describes the wrong company (collectible mystery boxes) — must
  be rewritten from the official site to drive a "iPhone charging diagnostic
  tool" voice.
- Excel `Research` sheet currently merges competitors + own-top — split into
  two sheets so item 1 and item 4 are visible separately.
- Own-top scraping is currently expected to go through Playwright MCP from
  the main session (slow, LLM-mediated). Replace with a Node Playwright
  script (subprocess, no MCP) for speed.
- `products[]` only has a generic `noir-mystery-box` entry — replace with
  MD-903 (red, charger/adapter tester) and MD-905 (black, charging cable
  tester), enabling theme-driven SKU selection at draft time.

## 2. Decisions

These are locked via the brainstorming Q&A on 2026-05-10:

| # | Decision |
|---|---|
| D1 | Keep `/weekly-plan` architecture; only refactor data flow. |
| D2 | Excel: split `Research` into `TopicResearch` + `OwnHistory` sheets. Final 6 sheets. `TopicResearch` = posts from rival product makers (not random people in the niche). |
| D3 | Own-top posts: Node Playwright script (`scripts/scrape-top-posts.mjs`), main-session sequential, shared profile dir. |
| D4 | "Own historical" = recent 60-90 posts ranked by engagement, top 10. Not cross-year history. |
| D5 | Refresh cadence: scrape every weekly-plan run; no caching layer. |
| D6 | `weekly-plan-review` (last-week metrics) stays on Playwright MCP. Only `OwnHistory` scraping moves to script. |
| D7 | Product info lives in brand YAML `products[]`. Single source of truth. |
| D8 | SKU rotation: `weekly-plan-draft` chooses `product_id` per slot at draft time, by theme fit. |
| D9 | SKU map: MD-903 = Adapter Tester (red, B0DZBZ9W55); MD-905 = Cable Tester (black, B0DZBSFV71). |
| D10 | Brand YAML fully rewritten from https://www.noirsboxes.com — target audience is repair shops, e-commerce sellers, QC, manufacturers, picky iPhone users. |

## 3. Final 6-sheet structure (`plan.xlsx`)

| # | Sheet | Maps to user item | Source | Approx rows |
|---|---|---|---|---|
| 1 | `TopicResearch` | ① competitor top-post analysis | `weekly-plan-research` (competitor side, fetch-reference + LLM) | 6 platforms × N competitors × 3 top ≈ 36–72 |
| 2 | `OwnHistory` | ④ own historical top | `scripts/scrape-top-posts.mjs` + LLM | 6 platforms × 10 ≈ 60 |
| 3 | `Frequency` | ② frequency / time | `weekly-plan-schedule` | 6 |
| 4 | `Schedule` | ⑤ drafts + schedule | `weekly-plan-schedule` + `weekly-plan-draft` | ~22 |
| 5 | `Metrics` | ③ last week's results | `weekly-plan-review` (MCP) | last week's posted slot count |
| 6 | `Meta` | run info | orchestrator | ~6 |

### Column reference

`TopicResearch`
```
platform | competitor_product | similar_to | relevant_to | post_url | posted_at |
likes | comments | shares | views |
hook | tone | layout | why_it_resonated | takeaway_for_us
```
- `competitor_product` = the rival product entry name (e.g. "ChargerLAB
  POWER-Z").
- `similar_to` = brand-level hint from YAML (md-903 | md-905).
- `relevant_to` = LLM's per-post determination from post content (md-903 |
  md-905 | both | neither). The downstream `weekly-plan-draft` filters by
  `relevant_to` not `similar_to` when picking insights for a given SKU.

`OwnHistory`
```
platform | post_url | posted_at | likes | comments | shares | views |
caption_excerpt | tone | layout | hook | why_it_resonated | repeatable_pattern
```

`Frequency`
```
platform | posts_per_week | preferred_weekdays | preferred_times | rationale
```

`Schedule`
```
slot_id | weekday | time_local | platform | mode | theme | product_id |
caption | hashtags | media_path | reference_urls | rationale |
status | posted_url | posted_at | draft_id
```

`Metrics`
```
slot_id | posted_url | metrics_captured_at | likes | reach | comments | saves | views | notes
```

`Meta`
```
brand | iso_week | generated_at | prev_week_plan | own_top_scraped_at | model | notes
```

`plan.json` is the canonical source of truth. `plan.xlsx` is regenerated from
it. Users edit `plan.json` and re-run `weekly-plan-export`, never edit xlsx
directly.

## 4. Brand YAML rewrite

Full content in section 1 of the brainstorming transcript; the contract
points are:

- `display_name`: "NoirsBoxes" (was "Black Magic Noir's Boxes" — kept only in
  social handles).
- `secondary_languages`: add `zh-CN` (Taobao market).
- `company.description`: charger / adapter / cable testing devices; B2B
  primary; tagline from official site.
- `voice.tone`: "technical, authoritative, solution-focused; problem-aware,
  not hypey".
- `voice.audience`: repair technicians; cross-border e-commerce sellers; QC
  / sourcing teams; charger / cable manufacturers; picky iPhone users.
- `voice.emphasis`: counterfeit detection, protocol identification (PD / QC
  / BC1.2), measurable evidence on TFT, MFi + E-Marker verification, dispute
  reduction, OTA updates.
- `voice.forbidden_behavior`: add "mystery / occult / collectible framing".
- `storefronts`: add `amazon_md903`, `amazon_md905`, `official`.
- `products[]`: full entries for MD-903 (red, adapter tester) and MD-905
  (black, cable tester) with `id / sku / name / color / category / url /
  selling_points / target_audience / suggested_themes`.
- `content_themes`: replace mystery / unboxing themes with technical demo
  themes (counterfeit detection demo, protocol explainer, lab readout
  close-up, dispute reduction story, MFi reveal, dead-cable autopsy, OTA
  update reveal).
- `content_style.<platform>.notes`: refit for technical voice (e.g. IG "first
  frame = TFT screen close-up").
- `media_library.hints`: replace "dark / moody / occult" with "TFT readout
  close-ups / lab desk / black + red product housings / before-after pairs".
- Replace flat `competitors[]` with `competitor_products[]`. Each entry:
  `{ name, similar_to (md-903 | md-905), category, region, socials: { fb, ig,
  x, threads, youtube, tiktok }, notes }`. Empty string per platform = skip
  that platform. `similar_to` is a brand-level hint (which of our SKUs this
  rival generally competes with). The actual per-post relevance is
  determined by LLM from post content at analysis time and stored as
  `relevant_to` on each TopicResearch row. Seeded by Claude via WebSearch +
  user approval (3 entries on 2026-05-10, see below); user maintains
  thereafter. If empty, `TopicResearch` sheet is written with header row
  only.

  Initial seed (locked 2026-05-10):
  ```yaml
  competitor_products:
    - name: "ChargerLAB POWER-Z"
      similar_to: md-903
      category: usb-pd-tester
      region: cn / global
      socials:
        facebook:  https://www.facebook.com/chargerlab/
        instagram: https://www.instagram.com/chargerlabs/
        x:         https://x.com/chargerlab
        youtube:   https://www.youtube.com/channel/UCbHlweun5NkTVDGmeqGmwjA
        tiktok:    https://www.tiktok.com/@chargerlab
        threads:   ""
      notes: "shared social handles with CT001 entry; scrape de-duplicates"

    - name: "ChargerLAB POWER-Z CT001"
      similar_to: md-905
      category: cable-tester
      region: cn / global
      socials:
        facebook:  https://www.facebook.com/chargerlab/
        instagram: https://www.instagram.com/chargerlabs/
        x:         https://x.com/chargerlab
        youtube:   https://www.youtube.com/channel/UCbHlweun5NkTVDGmeqGmwjA
        tiktok:    https://www.tiktok.com/@chargerlab
        threads:   ""
      notes: "same brand as POWER-Z; cable-side product line"

    - name: "Total Phase Advanced Cable Tester v2"
      similar_to: md-905
      category: cable-tester
      region: us
      socials:
        facebook:  https://www.facebook.com/totalphase/
        instagram: ""
        x:         https://x.com/totalphase
        youtube:   ""
        tiktok:    ""
        threads:   ""
      notes: "B2B-leaning; low social activity outside FB/X"
  ```

  Scrape de-duplication: when two entries share the same `socials.<platform>`
  URL, `weekly-plan-research` scrapes that account once and tags every row
  with the union of `similar_to` values from matching entries.

## 5. Node Playwright scrape script

### Files

```
scripts/
├── scrape-top-posts.mjs              # CLI entry point
└── scrapers/
    ├── facebook.mjs
    ├── instagram.mjs
    ├── x.mjs
    ├── threads.mjs
    ├── tiktok.mjs
    └── youtube.mjs
```

### CLI

```bash
node scripts/scrape-top-posts.mjs \
  --brand noirs-boxes \
  --platform <fb|ig|x|th|tt|yt|all> \
  --account-url <url> \
  --recent 60 \
  --top 10 \
  --out <path>
```

`--platform all` walks 6 platforms sequentially.

### Output JSON (per platform)

```json
{
  "platform": "instagram",
  "account_url": "...",
  "scraped_at": "<ISO>",
  "recent_count": 60,
  "top": [
    {
      "post_url": "...",
      "posted_at": "<ISO>",
      "media_type": "image|carousel|reel|video",
      "caption": "...",
      "hashtags": ["..."],
      "likes": 0, "comments": 0, "views": 0,
      "thumbnail_url": "..."
    }
  ]
}
```

LLM analysis (tone / hook / why_resonated / repeatable_pattern) happens in
the `weekly-plan-research` subagent that consumes this JSON, not in the
script.

### Profile lock policy

Node script and Playwright MCP cannot share the brand profile dir
concurrently. Orchestrator sequencing per §7: step 4 (last-week review,
MCP) ends with `browser_close` before step 5 (own-top scrape, script)
launches chromium. Steps 6–9 use subagents and do not touch the profile.
Single chromium user-data-dir, never parallel.

Out of scope: profile cloning, parallel-platform scraping. Reconsider if
single-platform scrape time exceeds 5 minutes.

### Anti-bot baseline

- `chromium.launchPersistentContext(profileDir, { headless: false })`.
- Random scroll delay 200–800ms.
- 1–2s pause every N posts.
- On captcha / login wall: stop, write partial JSON, exit non-zero with
  structured error. Do not retry, do not bypass. Caller surfaces the error
  per OPERATING_RULES §5.

### Logs

Script writes `data/scrape-logs/<run-id>-<platform>.jsonl` (one row per
navigate / scroll batch). Orchestrator records the script invocation in
`data/runs/<run-id>.meta.json` under `scrape_runs[]`. Action log
(`data/action-logs/`) stays MCP-only.

## 6. Skill / command / doc updates

| File | Change |
|---|---|
| `config/brands/noirs-boxes.yaml` | Full rewrite per §4. |
| `scripts/scrape-top-posts.mjs` | New. CLI entry point + dispatcher. |
| `scripts/scrapers/<6 platforms>.mjs` | New. One module per platform. |
| `scripts/plan-export.mjs` | Emit 6 sheets (split Research → TopicResearch + OwnHistory; add OwnHistory columns). |
| `.claude/skills/weekly-plan-research/SKILL.md` | own-post step changes from "main-session MCP scrape" to "shell out to scripts/scrape-top-posts.mjs"; competitor side unchanged. |
| `.claude/skills/weekly-plan-draft/SKILL.md` | Input adds `available_products[]`. Output adds `product_id`. Selection rule: match `slot.theme` against each product's `suggested_themes`; tie-break by alternation across the week. |
| `.claude/skills/weekly-plan-schedule/SKILL.md` | Schedule emits `product_id: null`; draft step fills it. Frequency rationale references prev-week metrics + own-top + competitor cadence when present. |
| `.claude/skills/weekly-plan-export/SKILL.md` | Realign with new sheet layout. |
| `.claude/commands/weekly-plan.md` | Insert step 5 ("own-top scrape, sequential") before competitor research. Update verification list. |
| `docs/WEEKLY_PLAN.md` | Sheet reference: replace Research with TopicResearch + OwnHistory. |
| `docs/OPERATING_RULES.md` | Add §11: "Playwright tool split — writes (publish/delete/login) via MCP; bulk read scraping via Node script. Profile dir is shared, never concurrent." |
| `CLAUDE.md` | Reflect §11; mention `data/scrape-logs/`. |
| `package.json` | Add `playwright` dep if missing; add npm script alias `scrape:top`. |

## 7. New `/weekly-plan` step list

```
1. Resolve target ISO week + brand.
2. mkdir reports/plans/<brand>/<iso_week>/research/
3. Generate run id; meta.mode = "weekly-plan".

4. [Last-week review] (only if prev plan exists with posted slots):
   - Main session runs weekly-plan-review (MCP, action-logged).
   - browser_close.

5. [Own-top scrape] (NEW):
   - Main session runs scripts/scrape-top-posts.mjs sequentially per
     platform. Writes research/own-<platform>-top.json.

6. [TopicResearch per platform] (subagent parallel):
   - For each platform, gather brand.competitor_products[].socials.<platform>
     URLs; de-duplicate (a single account may map to multiple entries);
     fetch-reference each public account; LLM analyses tone/hook/why per
     post + per-post `relevant_to` tag; writes research/topic-<platform>.json.

7. [Own-top analysis per platform] (subagent parallel):
   - Reads research/own-<platform>-top.json; LLM analyses; writes
     research/own-<platform>.json.

8. [Schedule] (main session compute):
   - frequency[] + schedule[]. slot.product_id = null.

9. [Drafts] (subagent parallel, one per slot):
   - Receives brand.products[] + slot.theme; chooses product_id; writes
     caption / hashtags / media_path / rationale.

10. [Compose plan.json + export plan.xlsx]:
    - Sheets: TopicResearch / OwnHistory / Frequency / Schedule / Metrics /
      Meta.

11. [Reply] per OPERATING_RULES §3 plain-text format.
```

## 8. Out of scope

- Cross-year historical mining (D4).
- Parallel platform scraping (D6 + §5 profile lock).
- Switching `weekly-plan-review` off MCP (D6).
- Auto-discovery of competitors (user fills `competitors[]`).
- New `/strategy` command.
- Editing xlsx directly (json is source of truth).
- Image generation pipeline changes (separate concern).
- Publish flow changes (`/publish-from-plan`, `/publish-now` unchanged).

## 9. Pre-deploy data the user must supply

`/weekly-plan` will run end-to-end without these, but the corresponding
sheets will be empty / sparse:

1. `competitor_products[]` in YAML — initial 3 entries seeded during
   brainstorming and locked above. User can extend (e.g. AVHzY / WITRN /
   FNIRSI when their socials are located, or add reviewer accounts as a
   distinct entry type later).
2. Brand assets in `media/assets/noirs-boxes/` — needed by `publish-*`, not
   by `/weekly-plan` itself.
3. (Optional) Per-SKU official product pages if separate from Amazon.

## 10. Acceptance criteria

- `config/brands/noirs-boxes.yaml` no longer mentions mystery / occult /
  collectible framing; both SKUs present with correct color + URL mapping.
- `node scripts/scrape-top-posts.mjs --platform instagram --top 5 --recent
  20` against the brand profile returns a valid JSON with at least one post,
  or a structured error.
- `/weekly-plan` (clean run, no prev plan) produces:
  - `reports/plans/noirs-boxes/<iso_week>/plan.json`
  - `reports/plans/noirs-boxes/<iso_week>/plan.xlsx` with 6 sheets, each
    sheet at least one row except `Metrics` (empty on first run) and
    `TopicResearch` (empty until user fills `competitors[]`).
- Each `Schedule` row has a non-null `product_id` (md-903 or md-905) chosen
  to match `theme`.
- `data/scrape-logs/<run-id>-<platform>.jsonl` written for each platform
  scraped.
- No regression in `/publish-from-plan` for an existing plan.

## 11. Risks

- Anti-bot escalation per platform — script may fail on IG / TikTok / YT.
  Mitigation: structured error, partial JSON, user surfaced.
- TopicResearch via fetch-reference is best-effort. IG / TikTok / Threads
  often gate public feeds behind login walls; YouTube channels and FB Pages
  are usually accessible. Expect sparse coverage on the gated platforms in
  v1; revisit if it becomes a blocker.
- LLM mis-classifies tone / hook / why for technical content (was tuned for
  collectible voice). Mitigation: brand YAML rewrite drives prompt, but
  expect 1–2 iterations after first run.
- Profile lock — accidental MCP-while-scraping. Mitigation: orchestrator
  enforces sequencing, OPERATING_RULES §11 documents it.
- SKU mismatch in YAML — if Amazon listings ever swap MD-903 / MD-905
  meaning. Mitigation: store explicit `sku + url + color` triple, not
  inferred.
