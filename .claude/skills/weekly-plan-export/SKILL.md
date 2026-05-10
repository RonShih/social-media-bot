---
name: weekly-plan-export
description: Convert plan.json into plan.xlsx via scripts/plan-export.mjs (exceljs).
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `plan_json_path`: absolute path to `reports/plans/<brand>/<iso_week>/plan.json`.

## Output
```json
{ "xlsx_path": "/abs/.../plan.xlsx" }
```

## Steps

1. Run:

   ```bash
   node scripts/plan-export.mjs <plan_json_path>
   ```

2. The script writes `plan.xlsx` next to `plan.json`. Confirm the file exists, return its absolute path.

3. If `node` is missing or `exceljs` is not installed → return `{ "error": "exceljs missing — run npm install in repo root" }`.

## Sheet structure (handled by the script)

- `Schedule`: per-slot rows.
- `Frequency`: per-platform cadence + rationale.
- `Research`: top-post analysis.
- `Metrics`: empty until `weekly-plan-review` populates it next week.
- `Meta`: brand, iso_week, generated_at, prev_week_plan_path, model, notes.

## Don'ts

- Do not modify `plan.json` here — this skill is one-way (json → xlsx). Edits to the plan happen via `weekly-plan-review` updating the JSON; xlsx is regenerated.
- Do not call `weekly-plan-import` from here.
- Do not parse xlsx in this skill — that's `scripts/plan-import.mjs`'s job.
