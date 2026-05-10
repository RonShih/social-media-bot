import { chromium } from "playwright";
import { mkdirSync, writeFileSync, appendFileSync } from "node:fs";
import { dirname } from "node:path";

export const SUPPORTED = ["facebook", "instagram", "x", "threads", "tiktok", "youtube"];

export function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
      out[k] = v;
    }
  }
  return out;
}

export async function withBrowser(profileDir, fn) {
  const ctx = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1280, height: 900 }
  });
  try {
    return await fn(ctx);
  } finally {
    await ctx.close();
  }
}

export function writeJson(outPath, payload) {
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify(payload, null, 2));
}

export function appendScrapeLog(runId, platform, entry) {
  const path = `data/scrape-logs/${runId}-${platform}.jsonl`;
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, JSON.stringify({ ts: new Date().toISOString(), ...entry }) + "\n");
}

export function structuredError(reason, step, extra = {}) {
  return { error: reason, step_failed: step, ...extra };
}

export async function jitter(min = 200, max = 800) {
  await new Promise((r) => setTimeout(r, min + Math.random() * (max - min)));
}
