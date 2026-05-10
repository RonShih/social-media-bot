#!/usr/bin/env node
// plan.xlsx -> plan.json shape. Used by /publish-from-plan to read the schedule.
// Usage: node scripts/plan-import.mjs <plan.xlsx>

import { existsSync, writeFileSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import ExcelJS from "exceljs";

const xlsxPath = resolve(process.argv[2] || "");
if (!xlsxPath || !existsSync(xlsxPath)) {
  console.error("usage: plan-import.mjs <path to plan.xlsx>");
  process.exit(2);
}

const wb = new ExcelJS.Workbook();
await wb.xlsx.readFile(xlsxPath);

function rows(sheetName) {
  const ws = wb.getWorksheet(sheetName);
  if (!ws) return [];
  const headers = ws.getRow(1).values.slice(1).map(String);
  const out = [];
  ws.eachRow({ includeEmpty: false }, (row, idx) => {
    if (idx === 1) return;
    const obj = {};
    row.values.slice(1).forEach((v, i) => {
      obj[headers[i]] = v ?? null;
    });
    out.push(obj);
  });
  return out;
}

function splitList(s, sep) {
  if (s == null || s === "") return [];
  if (Array.isArray(s)) return s;
  return String(s)
    .split(sep)
    .map((x) => x.trim())
    .filter(Boolean);
}

const plan = {
  schedule: rows("Schedule").map((r) => ({
    ...r,
    hashtags: splitList(r.hashtags, /\s+/),
    reference_urls: splitList(r.reference_urls, /\n/)
  })),
  frequency: rows("Frequency").map((r) => ({
    ...r,
    preferred_weekdays: splitList(r.preferred_weekdays, /,\s*/),
    preferred_times: splitList(r.preferred_times, /,\s*/)
  })),
  research: rows("Research"),
  metrics: rows("Metrics"),
  meta: Object.fromEntries(rows("Meta").map((r) => [r.key, r.value]))
};

const outPath = join(dirname(xlsxPath), "plan.imported.json");
writeFileSync(outPath, JSON.stringify(plan, null, 2));
console.log(outPath);
