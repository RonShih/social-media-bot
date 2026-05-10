#!/usr/bin/env node
// plan.json -> plan.xlsx (6 sheets: TopicResearch, OwnHistory, Frequency, Schedule, Metrics, Meta).
// Usage: node scripts/plan-export.mjs <plan.json>

import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import ExcelJS from "exceljs";

const planPath = resolve(process.argv[2] || "");
if (!planPath || !existsSync(planPath)) {
  console.error("usage: plan-export.mjs <path to plan.json>");
  process.exit(2);
}

const plan = JSON.parse(readFileSync(planPath, "utf8"));

// Filename = <iso_week>-<startMMDD>-<endMMDD>.xlsx (ISO week Mon → Sun).
function isoWeekRange(isoWeek) {
  const m = /^(\d{4})-W(\d{2})$/.exec(isoWeek || "");
  if (!m) return null;
  const year = Number(m[1]);
  const week = Number(m[2]);
  // ISO 8601: week 1 contains Jan 4. Find Mon of target week.
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const jan4Day = jan4.getUTCDay() || 7; // Sun=7
  const week1Mon = new Date(Date.UTC(year, 0, 4 - (jan4Day - 1)));
  const mon = new Date(week1Mon.getTime() + (week - 1) * 7 * 86400_000);
  const sun = new Date(mon.getTime() + 6 * 86400_000);
  const fmt = (d) => String(d.getUTCMonth() + 1).padStart(2, "0") + String(d.getUTCDate()).padStart(2, "0");
  return { startMMDD: fmt(mon), endMMDD: fmt(sun) };
}
const isoWeek = plan?.meta?.iso_week;
const range = isoWeekRange(isoWeek);
const xlsxName = range ? `${isoWeek}-${range.startMMDD}-${range.endMMDD}.xlsx` : "plan.xlsx";
const xlsxPath = join(dirname(planPath), xlsxName);
const wb = new ExcelJS.Workbook();
wb.creator = "social-media-bot";
wb.created = new Date();

const headerStyle = {
  font: { bold: true },
  fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFEFEFEF" } }
};

function addSheet(name, columns, rows) {
  const ws = wb.addWorksheet(name);
  ws.columns = columns.map((c) => ({ header: c.header, key: c.key, width: c.width || 20 }));
  ws.getRow(1).eachCell((cell) => Object.assign(cell, headerStyle));
  for (const r of rows || []) ws.addRow(r);
  ws.views = [{ state: "frozen", ySplit: 1 }];
  return ws;
}

addSheet(
  "TopicResearch",
  [
    { header: "platform", key: "platform", width: 12 },
    { header: "competitor_product", key: "competitor_product", width: 28 },
    { header: "similar_to", key: "similar_to", width: 12 },
    { header: "relevant_to", key: "relevant_to", width: 12 },
    { header: "post_url", key: "post_url", width: 50 },
    { header: "posted_at", key: "posted_at", width: 22 },
    { header: "likes", key: "likes", width: 8 },
    { header: "comments", key: "comments", width: 10 },
    { header: "shares", key: "shares", width: 8 },
    { header: "views", key: "views", width: 10 },
    { header: "hook", key: "hook", width: 40 },
    { header: "tone", key: "tone", width: 22 },
    { header: "layout", key: "layout", width: 30 },
    { header: "why_it_resonated", key: "why_it_resonated", width: 50 },
    { header: "takeaway_for_us", key: "takeaway_for_us", width: 50 }
  ],
  plan.topic_research || []
);

addSheet(
  "OwnHistory",
  [
    { header: "platform", key: "platform", width: 12 },
    { header: "post_url", key: "post_url", width: 50 },
    { header: "posted_at", key: "posted_at", width: 22 },
    { header: "likes", key: "likes", width: 8 },
    { header: "comments", key: "comments", width: 10 },
    { header: "shares", key: "shares", width: 8 },
    { header: "views", key: "views", width: 10 },
    { header: "caption_excerpt", key: "caption_excerpt", width: 50 },
    { header: "tone", key: "tone", width: 22 },
    { header: "layout", key: "layout", width: 30 },
    { header: "hook", key: "hook", width: 40 },
    { header: "why_it_resonated", key: "why_it_resonated", width: 50 },
    { header: "repeatable_pattern", key: "repeatable_pattern", width: 50 }
  ],
  plan.own_history || []
);

addSheet(
  "Frequency",
  [
    { header: "platform", key: "platform", width: 12 },
    { header: "posts_per_week", key: "posts_per_week", width: 14 },
    { header: "preferred_weekdays", key: "preferred_weekdays", width: 28 },
    { header: "preferred_times", key: "preferred_times", width: 22 },
    { header: "rationale", key: "rationale", width: 60 }
  ],
  (plan.frequency || []).map((r) => ({
    ...r,
    preferred_weekdays: Array.isArray(r.preferred_weekdays) ? r.preferred_weekdays.join(", ") : r.preferred_weekdays,
    preferred_times: Array.isArray(r.preferred_times) ? r.preferred_times.join(", ") : r.preferred_times
  }))
);

addSheet(
  "Schedule",
  [
    { header: "slot_id", key: "slot_id", width: 28 },
    { header: "weekday", key: "weekday", width: 8 },
    { header: "time_local", key: "time_local", width: 10 },
    { header: "platform", key: "platform", width: 12 },
    { header: "mode", key: "mode", width: 8 },
    { header: "theme", key: "theme", width: 22 },
    { header: "product_id", key: "product_id", width: 18 },
    { header: "caption", key: "caption", width: 60 },
    { header: "hashtags", key: "hashtags", width: 30 },
    { header: "media_path", key: "media_path", width: 36 },
    { header: "reference_urls", key: "reference_urls", width: 40 },
    { header: "status", key: "status", width: 10 },
    { header: "posted_url", key: "posted_url", width: 50 },
    { header: "posted_at", key: "posted_at", width: 22 },
    { header: "draft_id", key: "draft_id", width: 28 }
  ],
  (plan.schedule || []).map((s) => ({
    ...s,
    hashtags: Array.isArray(s.hashtags) ? s.hashtags.join(" ") : s.hashtags || "",
    reference_urls: Array.isArray(s.reference_urls) ? s.reference_urls.join("\n") : s.reference_urls || ""
  }))
);

addSheet(
  "Metrics",
  [
    { header: "slot_id", key: "slot_id", width: 28 },
    { header: "posted_url", key: "posted_url", width: 50 },
    { header: "metrics_captured_at", key: "metrics_captured_at", width: 22 },
    { header: "likes", key: "likes", width: 8 },
    { header: "reach", key: "reach", width: 10 },
    { header: "comments", key: "comments", width: 10 },
    { header: "saves", key: "saves", width: 8 },
    { header: "notes", key: "notes", width: 40 }
  ],
  plan.metrics || []
);

addSheet(
  "Meta",
  [
    { header: "key", key: "key", width: 22 },
    { header: "value", key: "value", width: 80 }
  ],
  Object.entries(plan.meta || {}).map(([key, value]) => ({
    key,
    value: typeof value === "string" ? value : JSON.stringify(value)
  }))
);

await wb.xlsx.writeFile(xlsxPath);
console.log(xlsxPath);
