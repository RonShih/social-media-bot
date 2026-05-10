#!/usr/bin/env node
// Pretty-print a run from data/action-logs/<run-id>.jsonl + data/runs/<run-id>.meta.json.
// Usage: node scripts/action-log-summarize.mjs <run-id>

import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const runId = process.argv[2];
if (!runId) {
  console.error("usage: action-log-summarize.mjs <run-id>");
  process.exit(2);
}

const repo = resolve(new URL("..", import.meta.url).pathname);
const jsonlPath = resolve(repo, "data/action-logs", `${runId}.jsonl`);
const metaPath = resolve(repo, "data/runs", `${runId}.meta.json`);

if (!existsSync(jsonlPath)) {
  console.error(`not found: ${jsonlPath}`);
  process.exit(1);
}

const lines = readFileSync(jsonlPath, "utf8").split("\n").filter(Boolean);
const meta = existsSync(metaPath) ? JSON.parse(readFileSync(metaPath, "utf8")) : null;

if (meta) {
  console.log(`run_id      ${meta.run_id}`);
  console.log(`mode        ${meta.mode}`);
  console.log(`brand       ${meta.brand}`);
  console.log(`platforms   ${(meta.platforms || []).join(", ")}`);
  console.log(`draft_id    ${meta.draft_id || "-"}`);
  console.log(`started_at  ${meta.started_at}`);
  console.log(`ended_at    ${meta.ended_at}`);
  console.log(`status      ${meta.status}`);
  console.log("");
  console.log("outcomes:");
  for (const o of meta.outcomes || []) {
    const tag = o.status === "success" ? "OK " : o.status === "needs_verify" ? "?? " : "ER ";
    console.log(`  ${tag} ${o.platform.padEnd(10)} ${o.post_url || o.error || ""}`);
  }
  console.log("");
}

console.log(`steps (${lines.length}):`);
for (const line of lines) {
  let entry;
  try {
    entry = JSON.parse(line);
  } catch {
    console.log(`  [parse error] ${line.slice(0, 120)}`);
    continue;
  }
  const tag = entry.result === "ok" ? "OK" : "ER";
  const idx = String(entry.step_idx).padStart(3, " ");
  const platform = (entry.platform || "-").padEnd(10);
  const tool = (entry.tool || "").replace("mcp__playwright__", "").padEnd(22);
  const dur = `${entry.duration_ms ?? 0}ms`.padStart(7);
  console.log(`  ${idx} ${tag} ${platform} ${tool} ${dur}  ${entry.step_label}`);
  if (entry.result === "err") {
    if (entry.note) console.log(`        note: ${entry.note}`);
    if (entry.screenshot) console.log(`        shot: ${entry.screenshot}`);
  }
}
