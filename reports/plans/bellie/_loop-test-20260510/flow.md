# /loop 5m simulation — flow log

- run_id: 20260510-003200-loop
- mode: loop-test (no real publish, no Playwright)
- plan: reports/plans/bellie/_loop-test-20260510/plan.json
- action log: data/action-logs/20260510-003200-loop.jsonl
- meta: data/runs/20260510-003200-loop.meta.json
- started: 2026-05-10 00:32 CST (Sun)
- ended:   2026-05-10 00:55 CST (Sun)
- duration: ~23 min
- result: 5/5 today's slots fake-posted ✅

## Tick-by-tick

| tick | wall clock | slot fired | scheduled for | latency | progress |
|---|---|---|---|---|---|
| 0 (sanity) | 00:34:57 | test-loop-fb-sun-0034 | 00:34 | <1 min | 1/5 |
| 1 | 00:40:06 | test-loop-ig-sun-0039 | 00:39 | 1 min  | 2/5 |
| 2 | 00:45:06 | test-loop-fb-sun-0044 | 00:44 | 1 min  | 3/5 |
| 3 | 00:50:04 | test-loop-ig-sun-0049 | 00:49 | 1 min  | 4/5 |
| 4 | 00:55:05 | test-loop-fb-sun-0054 | 00:54 | 1 min  | 5/5 |

## What this validated

1. **`/loop 5m` cadence works** — 5 ticks at exact 5-min intervals (one initial sanity tick + 4 ScheduleWakeup-driven ticks). No drift.
2. **Time-window filtering correct** — each tick only fired slots whose `time_local ≤ now AND status != fake-posted`. No double-firing, no premature firing, no missed slot.
3. **Worst-case latency = 1 minute** — every slot picked up on the next tick after its scheduled time. Within the 5-min `/loop` cadence promise.
4. **Idempotency** — the `status: fake-posted` flag prevents re-firing on subsequent ticks. Even if a tick happens to run after multiple due slots accumulate (e.g. machine sleep), they all get caught up in `time_local` order.

## What this did NOT exercise

- Real `publish-<platform>` flows — `dry-tick.mjs` only flips status; it does not open a browser.
- The `/publish-from-plan` orchestrator's two-stage gate (TG / Line confirmation flow).
- Re-export of `plan.xlsx` after status flip (real `/publish-from-plan` re-runs `weekly-plan-export`; the test skipped this).

## How to switch from sim → real

The test ticks call:
```bash
node scripts/dry-tick.mjs <plan.json> <run_id>
```

Real production tick should call instead:
```bash
claude /publish-from-plan --day today
```

So the production loop launcher is:
```
/loop 5m /publish-from-plan --day today
```

`/publish-from-plan --day today` does internally what `dry-tick.mjs` proved here (filter slots by weekday + time_local + status), then dispatches `publish-<platform>` for each due slot, then re-exports the xlsx.

## Cleanup

Test plan + run meta + action log can be archived/deleted at any time without affecting the real W19 plan. Quick check:

```bash
rm -rf reports/plans/bellie/_loop-test-20260510/
rm data/runs/20260510-003200-loop.meta.json
rm data/action-logs/20260510-003200-loop.jsonl
```

Real W19 production data lives at `reports/plans/bellie/2026-W19/` — untouched throughout this test.
