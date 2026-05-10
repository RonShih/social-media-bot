#!/usr/bin/env node
// Loop simulator — reads a plan.json, finds slots whose weekday=today AND
// time_local ≤ now AND status != fake-posted, marks them, writes one line per
// fired slot to data/action-logs/<run_id>.jsonl.
// Does NOT touch real publish-* flows. Pure timing/dispatch demo.
//
// Usage:
//   node scripts/dry-tick.mjs <plan.json> <run_id>

import { readFileSync, writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";

const planPath = resolve(process.argv[2] || "");
const runId = process.argv[3];
if (!planPath || !existsSync(planPath) || !runId) {
  console.error("usage: dry-tick.mjs <plan.json> <run_id>");
  process.exit(2);
}

const plan = JSON.parse(readFileSync(planPath, "utf8"));
const now = new Date();
const todayWeekday = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][now.getDay()];
const nowHHMM = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

const dueNow = (plan.schedule || []).filter((s) => {
  if (s.status === "fake-posted") return false;
  if (s.weekday !== todayWeekday) return false;
  return s.time_local <= nowHHMM;
});

const logPath = `data/action-logs/${runId}.jsonl`;
mkdirSync(dirname(logPath), { recursive: true });

const tickTs = now.toISOString();
const fired = [];
for (const slot of dueNow) {
  slot.status = "fake-posted";
  slot.posted_at = tickTs;
  slot.posted_url = `dryrun://simulated/${slot.slot_id}`;
  const line = JSON.stringify({
    ts: tickTs,
    run_id: runId,
    brand: plan.meta?.brand || "unknown",
    platform: slot.platform,
    step_idx: 0,
    step_label: "fake-publish",
    tool: "scripts/dry-tick.mjs",
    args: { slot_id: slot.slot_id, time_local: slot.time_local },
    result: "ok",
    duration_ms: 0,
    note: `fake-posted at tick ${nowHHMM} (slot scheduled for ${slot.time_local})`,
  });
  appendFileSync(logPath, line + "\n");
  fired.push(slot.slot_id);
}

writeFileSync(planPath, JSON.stringify(plan, null, 2));

const total = (plan.schedule || []).filter((s) => s.weekday === todayWeekday).length;
const done = (plan.schedule || []).filter((s) => s.weekday === todayWeekday && s.status === "fake-posted").length;

console.log(JSON.stringify({
  tick_at: tickTs,
  weekday: todayWeekday,
  now_HHMM: nowHHMM,
  fired_this_tick: fired,
  progress: `${done}/${total} today's slots fake-posted`,
}, null, 2));
