#!/usr/bin/env node
// Own-account top-post scraper. Dispatches to scripts/scrapers/<platform>.mjs.
// Usage: node scripts/scrape-top-posts.mjs --brand <slug> --platform <p>
//        --account-url <url> [--recent 60] [--top 10] [--out <path>]

import { parseArgs, SUPPORTED, writeJson, structuredError } from "./scrapers/_shared.mjs";

const args = parseArgs(process.argv);

if (!args.platform) { process.stderr.write("--platform required\n"); process.exit(2); }
if (!SUPPORTED.includes(args.platform)) {
  process.stderr.write(`unknown platform: ${args.platform}\n`);
  process.exit(2);
}
if (!args["account-url"]) { process.stderr.write("--account-url required\n"); process.exit(2); }

const recent = Number(args.recent || 60);
const top = Number(args.top || 10);
const brand = args.brand || "default";
const profileDir = args["profile-dir"] || `browser_profiles/${brand}`;
const outPath = args.out || `reports/scrape-out/${brand}-${args.platform}-top.json`;
const runId = args["run-id"] || `${new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14)}-cli`;

let mod;
try {
  mod = await import(`./scrapers/${args.platform}.mjs`);
} catch (e) {
  process.stderr.write(`scraper module not implemented for ${args.platform}: ${e.message}\n`);
  process.exit(3);
}

try {
  const result = await mod.scrape({
    accountUrl: args["account-url"],
    recent,
    top,
    profileDir,
    runId
  });
  writeJson(outPath, result);
  process.stdout.write(outPath + "\n");
} catch (e) {
  const err = structuredError(e.message || String(e), "scrape", { platform: args.platform });
  writeJson(outPath, err);
  process.stderr.write(JSON.stringify(err) + "\n");
  process.exit(1);
}
