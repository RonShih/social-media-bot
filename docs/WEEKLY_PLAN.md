# Weekly plan

End-to-end weekly content workflow. Lives at `reports/plans/<brand>/<YYYY-Www>/`.

## Files per week

```
reports/plans/<brand>/2026-W19/
├── plan.json           # source of truth (machine-readable)
├── plan.xlsx           # human-readable, regenerated from plan.json
└── research/           # raw per-platform research JSON
    ├── facebook.json
    ├── instagram.json
    ├── x.json
    ├── threads.json
    ├── youtube.json
    └── tiktok.json
```

`plan.json` is canonical. `plan.xlsx` is a view; treat it as read-only from the user's side. Edits to the plan happen by editing `plan.json` and re-running `weekly-plan-export`.

## Generation pipeline

`/weekly-plan` orchestrates these steps:

1. **Last-week review** (only if a previous plan exists with at least one `posted` slot):
   - `weekly-plan-review` re-visits each `posted_url` via the logged-in browser.
   - Writes fresh rows to last week's `Metrics` sheet.
   - Updates `data/stats-history/<brand>.json`.

2. **Research per platform** (parallel):
   - One `weekly-plan-research` subagent per platform.
   - Subagent does competitor analysis via `fetch-reference`. Own-post analysis runs in the main session (Playwright cannot reach subagents).
   - Per-platform output saved as `research/<platform>.json`.

3. **Schedule** (main session, pure compute):
   - `weekly-plan-schedule` produces `frequency[]` and `schedule[]` for the week.
   - Last-week `Metrics` (if available) nudge frequency / time bands.

4. **Drafts** (parallel):
   - One `weekly-plan-draft` subagent per slot.
   - Each subagent receives `research_rows` filtered to its platform + the brand YAML.
   - Returns caption / hashtags / media_path / reference_urls / rationale.

5. **Compose** `plan.json` and call `weekly-plan-export` for `plan.xlsx`.

## Sheet reference

### Schedule

One row per scheduled post.

```
slot_id, weekday, time_local, platform, mode, theme, product_id,
caption, hashtags, media_path, reference_urls,
status, posted_url, posted_at, draft_id
```

`status`: `planned | posted | failed | needs_verify | skipped`. Updated by `/publish-from-plan`.

`slot_id` format: `<iso_week>-<plat3>-<wk3>-<HHMM>` (e.g. `2026-W19-ig-mon-1230`).

### Frequency

Per-platform cadence used for this week.

```
platform, posts_per_week, preferred_weekdays, preferred_times, rationale
```

### Research

Top-post analysis. `source` is `own | competitor`. `tone`, `layout`, `hook`, `why_it_resonated` are the LLM's structured read.

### Metrics

Populated next week by `weekly-plan-review`. Never populated in the same run that creates the plan.

```
slot_id, posted_url, metrics_captured_at, likes, reach, comments, saves, notes
```

### Meta

Key/value rows: `brand`, `iso_week`, `generated_at`, `prev_week_plan_path`, `model`, `notes`.

## Day-of execution

`/publish-from-plan --day today` reads `Schedule`, filters to today's weekday, processes due slots in time order. For each slot:

- Materializes a `reports/drafts/<brand>/<draft_id>.json` so `/publish-now`-style downstream tooling works.
- Runs `publish-<platform>` exactly like `/publish-now` (action-logged).
- Updates `Schedule[slot_id].status / posted_url / posted_at` in `plan.json`.
- Re-exports `plan.xlsx`.

## Two-stage gate (channel sessions)

In a Telegram / Line / channel session, `/publish-from-plan` honors the same gate as `/publish-now`:

1. First reply: preview of due slots (plain text, no markdown).
2. Write entry to `data/pending-confirmations.json` (5 min TTL).
3. User replies `ok` / `go` / `yes` / `/publish-from-plan ...` → execute.
4. Multiple drafts pending → require explicit slash form.

Terminal invocations skip the gate (the user typed the command themselves).

## Feedback loop (week N → week N+1)

When `/weekly-plan` runs for week `N+1`:

1. It looks for `reports/plans/<brand>/<N>/plan.json`. If present and has any `posted` slots → call `weekly-plan-review`.
2. Updated metrics flow into `data/stats-history/<brand>.json`.
3. `weekly-plan-schedule` reads the rolled-up history when computing week `N+1`'s frequency / time bands.

The nudges are gentle (see `weekly-plan-schedule` SKILL.md heuristics) — at least 4 data points per band before changing a recommendation, no week-to-week swings.

## Caveats

- Engagement metrics drift over time (likes accrue, view counts climb). `metrics_captured_at` is a snapshot.
- Some platforms hide reach / saves unless logged in as page owner. The own-post review is best-effort.
- Competitor scraping is `fetch-reference`-only (no logged-in scraping). Counts are sometimes hidden — fall back on the qualitative `tone / layout / hook` analysis.
- TikTok and YouTube re-auth occasionally blocks `weekly-plan-review` mid-run; the orchestrator surfaces and stops rather than retrying.
