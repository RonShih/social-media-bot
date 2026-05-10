---
name: weekly-plan-schedule
description: Compute per-platform posting frequency and best-time slots for the week. Outputs a schedule grid the draft step fills in.
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `brand`: active brand slug.
- `iso_week`: target week, e.g. `2026-W19` (Mon-Sun).
- `research_summary`: aggregated research data (the merged output of `weekly-plan-research` runs).
- `prev_metrics`: optional — last week's `Metrics` rows from `reports/plans/<brand>/<prev iso_week>/plan.json`. Used to nudge frequency / timing.
- `brand_style`: `content_style` from the brand YAML.

## Output (JSON)

```json
{
  "iso_week": "2026-W19",
  "frequency": [
    {
      "platform": "instagram",
      "posts_per_week": 4,
      "preferred_weekdays": ["Mon", "Wed", "Fri", "Sun"],
      "preferred_times": ["12:30", "20:00"],
      "rationale": "..."
    }
  ],
  "schedule": [
    {
      "slot_id": "2026-W19-ig-mon-1230",
      "weekday": "Mon",
      "time_local": "12:30",
      "platform": "instagram",
      "mode": "post",
      "theme": "<from content_themes>",
      "product_id": "noir-mystery-box"
    }
  ]
}
```

## Heuristics

Default cadence (override via `prev_metrics` or brand-specific YAML in the future):

| platform | posts_per_week | preferred_weekdays | preferred_times (local) |
|---|---|---|---|
| facebook | 3 | Tue, Thu, Sat | 11:00, 19:00 |
| instagram | 4 | Mon, Wed, Fri, Sun | 12:30, 20:00 |
| x | 7 | every day | 09:00 |
| threads | 4 | Mon, Wed, Fri, Sat | 21:00 |
| youtube | 1 | Sat | 16:00 |
| tiktok | 3 | Tue, Thu, Sat | 19:00 |

`prev_metrics` adjustment rules (apply when last-week data is provided):

- A platform's posts that landed in a `time_local` band averaging > 2x the brand mean engagement → add that band to `preferred_times` for next week.
- A platform with last-week mean engagement in the bottom quartile of its own historical mean → **decrease** `posts_per_week` by 1 (floor: 1).
- A weekday with consistently zero engagement on 3+ recent posts → drop from `preferred_weekdays`.

These nudges are gentle — do not flip cadence wildly week-over-week. Confidence threshold: at least 4 data points per band before changing.

## Slot id format

`<iso_week>-<platform-3letter>-<weekday-3letter>-<HHMM>`

Examples: `2026-W19-ig-mon-1230`, `2026-W19-yt-sat-1600`.

## Theme + product assignment

- Pull `theme` from `content_themes[]`. Round-robin within the week so the brand does not post the same theme back-to-back on the same platform.
- Pull `product_id` from `products[]`. If multiple products, distribute proportionally; if none (`products: []`), set `product_id: null`.

## Don'ts

- Do not generate captions or hashtags here — that's `weekly-plan-draft`.
- Do not create slots outside `iso_week`.
- Do not write files — return JSON only.
- Do not call other skills.
- Do not assume `prev_metrics` is present — fall back to default cadence.
