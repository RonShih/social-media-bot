---
name: weekly-plan-review
description: Re-visit posted URLs from the previous week's plan and scrape current likes / reach into the Metrics sheet.
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `prev_plan_json_path`: `reports/plans/<brand>/<prev iso_week>/plan.json`.

## Output
```json
{
  "metrics_added": 12,
  "stats_history_updated": true
}
```

## Steps

1. Load `prev_plan_json_path`. Iterate `Schedule` rows with `status: posted` and a `posted_url`.
2. For each row, navigate to `posted_url` with the logged-in Playwright session and read public engagement metrics:
   - facebook: likes/reactions, comments, shares (visible on the post card).
   - instagram: likes (post), views (Reel), comments. Saves are visible only in Insights — skip if not exposed.
   - x: likes, replies, reposts, views.
   - threads: likes, replies, reposts (no view counts as of plan-write).
   - youtube: views (visible on watch page), likes (toggle if hidden).
   - tiktok: views, likes, comments, shares.
3. Append a row to `Metrics`:

   ```json
   {
     "slot_id": "<from Schedule>",
     "posted_url": "...",
     "metrics_captured_at": "<ISO>",
     "likes": 123,
     "reach": 4567,
     "comments": 12,
     "saves": null,
     "notes": ""
   }
   ```

4. Roll up into `data/stats-history/<brand>.json`:

   ```json
   {
     "brand": "noirs-boxes",
     "by_platform": {
       "instagram": {
         "totals_by_iso_week": { "2026-W18": { "likes": ..., "reach": ..., "post_count": 4 } },
         "by_weekday": { "Mon": { "mean_likes": ..., "n": ... } },
         "by_time_band": { "20:00-21:00": { "mean_likes": ..., "n": ... } }
       }
     }
   }
   ```

5. Save the updated `plan.json` and re-export to `plan.xlsx` via `weekly-plan-export`.

6. `mcp__playwright__browser_close`.

## Quirks

- Many platforms hide exact view counts unless logged in as the page owner. The logged-in profile already covers own pages — that's why this is "own posts only".
- Some metrics drift over weeks (likes accrue, view counts climb). Capture the snapshot at the time of review and rely on `metrics_captured_at` to interpret freshness.

## Don'ts

- Do not scrape competitor accounts — they live in research, not metrics.
- Do not write to `posted_url` rows from a plan that was never published (`status != posted`).
- Do not call other skills except `weekly-plan-export`.
- Do not skip `browser_close`.
