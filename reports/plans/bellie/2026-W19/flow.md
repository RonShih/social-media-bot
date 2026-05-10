# /weekly-plan flow log — bellie / 2026-W19

- run_id: 20260509-142401-eddb
- brand: bellie
- iso_week: 2026-W19
- started_at: 2026-05-09T14:24:01Z
- action_log: data/action-logs/20260509-142401-eddb.jsonl
- meta: data/runs/20260509-142401-eddb.meta.json

Each row = one component fired. `kind` = command / skill / subagent / script / tool. Top-down execution order.

| step | kind | name | invoked from | inputs | output |
|---|---|---|---|---|---|
| 0 | command | /weekly-plan | terminal | brand=bellie, week=current | run_id, plan_dir |
| 1 | shell | `date +%G-W%V` | main | — | iso_week=2026-W19 |
| 2 | fs | mkdir reports/plans/bellie/2026-W19/research | main | — | dir created |
| 3 | fs | write data/runs/<run_id>.meta.json | main | meta json | meta file |
| 4 | check | prev plan at reports/plans/bellie/2026-W18/plan.json | main | — | NOT_FOUND |
| 5 | skill | weekly-plan-review | main | — | **SKIPPED** — no previous-week plan |
| 6 | check | brand YAML socials.* | main | bellie.yaml | FB ✅ IG ✅ X ❌ Threads ❌ YT ❌ TikTok ❌ (empty url) |
| 7 | check | brand YAML competitors[] / reference_urls.competitors[] | main | bellie.yaml | empty → no competitor research |
| 8 | subagent | weekly-plan-research × competitors | (would-be) main | competitor URLs | **SKIPPED** — none configured; no fetch-reference subagents spawned |
| 9 | platform-loop | own-post research | main | FB, IG only | proceeding sequentially (browser session does not propagate to subagents) |
| 10 | tool | mcp__playwright__browser_navigate | main | FB profile URL | page loaded |
| 11 | tool | mcp__playwright__browser_snapshot (target=e690, depth=10) | main | accessibility tree | 2 posts captured |
| 12 | skill | weekly-plan-research (FB own) | main | snapshot | research/facebook.json (2 rows) |
| 13 | tool | mcp__playwright__browser_navigate | main | IG profile URL | page loaded |
| 14 | tool | mcp__playwright__browser_evaluate | main | grid query | 0 tiles (initial) |
| 15 | tool | mcp__playwright__browser_snapshot | main | full tree | 12 tiles via alt-text fallback |
| 16 | skill | weekly-plan-research (IG own) | main | snapshot | research/instagram.json (5 rows) |
| 17 | tool | mcp__playwright__browser_close | main | — | ok |
| 18 | skill | weekly-plan-schedule | main (no subagent — pure compute) | research summary, brand_style, no prev_metrics | 6 frequency rows + 7 schedule slots |
| 19 | subagent | weekly-plan-draft (×7 in parallel) | main → 7× general-purpose subagents | slot, research_rows, brand_yaml, draft-<platform>/SKILL.md | 7 caption JSONs |
| 19a | subagent | weekly-plan-draft / 2026-W19-fb-tue-1100 | id aa9ada0f0df714b8b | — | OK, media_path null |
| 19b | subagent | weekly-plan-draft / 2026-W19-fb-thu-1900 | id a06dca94bf6a3725d | — | OK, media_path null |
| 19c | subagent | weekly-plan-draft / 2026-W19-fb-sat-1100 | id ad4d4535a9bec1297 | — | OK, media_path null |
| 19d | subagent | weekly-plan-draft / 2026-W19-ig-mon-1230 | id a9464ab4c364c764e | — | OK, media_path null |
| 19e | subagent | weekly-plan-draft / 2026-W19-ig-wed-2000 | id af24f33c31d0b7800 | — | OK, **media_path = bellie-rainy-day.mp4** |
| 19f | subagent | weekly-plan-draft / 2026-W19-ig-fri-1230 | id ad70a7d3ef54cc0b2 | — | OK, media_path null |
| 19g | subagent | weekly-plan-draft / 2026-W19-ig-sun-2000 | id aa5972879f661d0ce | — | OK, media_path null |
| 20 | fs | write reports/plans/bellie/2026-W19/plan.json | main | aggregated json | 12.3 KB |
| 21 | shell | npm install | main | package.json (exceljs ^4.4.0 declared, missing) | 97 packages added |
| 22 | skill | weekly-plan-export | main | plan.json | plan.xlsx (13.2 KB) |
| 23 | script | scripts/plan-export.mjs | called by skill | plan_json_path | xlsx_path |
| 24 | fs | update data/runs/<run_id>.meta.json with end-state | main | outcomes | meta finalized |
| 25 | fs | finalize flow.md | main | this file | done |

## Skill / component inventory

Total components fired in this run:

| component | category | invocations |
|---|---|---|
| `/weekly-plan` (command) | command | 1 |
| `weekly-plan-research` skill | skill | 2 (FB, IG, main session — would be subagent for competitors but none configured) |
| `weekly-plan-schedule` skill | skill | 1 |
| `weekly-plan-draft` skill | skill (in subagent) | 7 |
| `weekly-plan-export` skill | skill | 1 |
| `weekly-plan-review` skill | skill | 0 (skipped — no prev plan) |
| `fetch-reference` skill | skill (in subagent) | 0 (skipped — no competitors) |
| `general-purpose` subagent | subagent | 7 |
| `mcp__playwright__browser_*` | tool (Playwright MCP) | 6 calls (2 navigate, 3 evaluate, 1 close + snapshots) |
| `scripts/plan-export.mjs` | script | 1 |
| `npm install` | shell | 1 (first-run dep install) |

## Outputs

- `reports/plans/bellie/2026-W19/plan.json` — source of truth (12.3 KB)
- `reports/plans/bellie/2026-W19/plan.xlsx` — 5 sheets (Schedule / Frequency / Research / Metrics / Meta) (13.2 KB)
- `reports/plans/bellie/2026-W19/research/facebook.json` — 2 own-post rows
- `reports/plans/bellie/2026-W19/research/instagram.json` — 5 own-post rows
- `data/action-logs/20260509-142401-eddb.jsonl` — 5 Playwright lines
- `data/runs/20260509-142401-eddb.meta.json` — run summary

## Caveats this run surfaced

1. Brand YAML has empty `socials.url` for X / Threads / YouTube / TikTok → those 4 platforms produced 0 slots. `/setup` to fill them in.
2. Brand YAML has empty `competitors[]` and `reference_urls.competitors[]` → no competitor research; analysis is own-only.
3. `media/assets/bellie/` only has 1 video (`bellie-rainy-day.mp4`); 6 of 7 slots have `media_path: null` and need `image-generator` or owner upload before publish.
4. No previous plan → no Metrics-sheet feedback loop this run; next week's `/weekly-plan` will start the loop if posts ship from this plan.
5. `npm install` was needed on first run because `node_modules/` wasn't checked in. Subsequent `/weekly-plan` runs will skip this step.

