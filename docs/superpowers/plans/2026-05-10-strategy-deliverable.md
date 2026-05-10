# Strategy Deliverable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/weekly-plan` produce a single 6-sheet `plan.xlsx` covering competitor product analysis, frequency/timing, last-week metrics, own historical top posts, and the upcoming week's drafted schedule for noirsboxes (MD-903 + MD-905).

**Architecture:** Keep existing `/weekly-plan` orchestration. Rewrite brand YAML to match the real product line (charger / cable testers, B2B). Split the Excel `Research` sheet into `TopicResearch` (rival product makers) and `OwnHistory` (auto-scraped own top). Move own-account scraping from Playwright MCP to a Node Playwright script under `scripts/scrape-top-posts.mjs` for speed; competitor scraping stays on `fetch-reference`. Browser profile is shared and serialized — script and MCP never touch the brand profile concurrently.

**Tech Stack:** Node 18+ ESM, Playwright (chromium, persistent context), ExcelJS, YAML (the project already has it via the brand profile loader). Spec lives at `docs/superpowers/specs/2026-05-10-strategy-deliverable-design.md` — read alongside this plan.

**Repo state note:** The working directory is not a git repository at plan-write time. The plan includes `git add` / `git commit` steps assuming the user runs `git init` first; if the user prefers not to use git, the implementer should replace each commit step with a manual checkpoint (note completion, move on).

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Modify | `config/brands/noirs-boxes.yaml` | Brand profile rewritten to charger/cable tester voice; MD-903 + MD-905 products; locked competitor_products[] (3). |
| Modify | `scripts/plan-export.mjs` | Emit 6 sheets: TopicResearch, OwnHistory, Frequency, Schedule, Metrics, Meta. |
| Create | `scripts/scrape-top-posts.mjs` | CLI entry point for own-account top-post scraping. Dispatches to per-platform module. |
| Create | `scripts/scrapers/_shared.mjs` | Browser launch helper (persistent context, headed), JSON output writer, structured-error helper, scrape-log writer. |
| Create | `scripts/scrapers/instagram.mjs` | IG own-account top-post scraper. |
| Create | `scripts/scrapers/facebook.mjs` | FB Page own-account scraper. |
| Create | `scripts/scrapers/x.mjs` | X own-account scraper. |
| Create | `scripts/scrapers/threads.mjs` | Threads own-account scraper. |
| Create | `scripts/scrapers/tiktok.mjs` | TikTok own-account scraper. |
| Create | `scripts/scrapers/youtube.mjs` | YouTube channel own-account scraper. |
| Create | `tests/plan-export.test.mjs` | Unit test: 6 sheets, correct columns, sample data round-trip. |
| Create | `tests/scrape-cli.test.mjs` | Unit test: CLI arg validation, dispatcher routing, structured error output. |
| Create | `tests/scraper-instagram-parse.test.mjs` | Unit test: IG post-card parser against fixture HTML. |
| Create | `tests/fixtures/instagram-feed.html` | Saved minimal HTML snippet of an IG profile feed page. |
| Modify | `.claude/skills/weekly-plan-research/SKILL.md` | Own-post path: shell out to `scripts/scrape-top-posts.mjs`. Competitor path: de-duplicate URLs, tag relevant_to per post. |
| Modify | `.claude/skills/weekly-plan-draft/SKILL.md` | Accept `available_products[]`; output `product_id`; selection by `slot.theme` ↔ `product.suggested_themes`. |
| Modify | `.claude/skills/weekly-plan-schedule/SKILL.md` | Schedule emits `product_id: null` (draft step fills it). Frequency rationale wired to research + prev_metrics. |
| Modify | `.claude/skills/weekly-plan-export/SKILL.md` | Sheet structure section reflects the 6 sheets. |
| Modify | `.claude/commands/weekly-plan.md` | Insert "Step 5: own-top scrape (sequential, script)". |
| Modify | `docs/WEEKLY_PLAN.md` | Sheet reference: replace Research with TopicResearch + OwnHistory. |
| Modify | `docs/OPERATING_RULES.md` | Add §11 "Playwright tool split". |
| Modify | `CLAUDE.md` | Reflect §11; mention `data/scrape-logs/`. |
| Modify | `package.json` | Add `playwright` dep; add npm scripts `scrape:top` and `test`. |

---

## Task 1: Rewrite brand YAML (noirs-boxes)

**Files:**
- Modify: `config/brands/noirs-boxes.yaml` (full rewrite)

- [ ] **Step 1: Rewrite the file**

Replace the entire file with the content below. Source: design spec §4 + locked competitor_products[].

```yaml
brand:
  slug: noirs-boxes
  display_name: "NoirsBoxes"
  primary_language: en
  secondary_languages: [zh-TW, ja, zh-CN]

company:
  description: |
    Taiwan-based maker of intelligent charger / adapter / cable testing devices.
    Tagline: "Stop damaging your devices with fake chargers — let NoirsBoxes
    reveal the truth behind every cable." Products detect protocols (PD, QC),
    measure voltage / current / ripple noise, verify MFi certification, and
    identify counterfeit accessories. Sold globally via Amazon US, Taobao, and
    Rakuten JP; primary B2B customers are repair shops, e-commerce sellers
    (Amazon / eBay / Shopee), QC departments, and charger manufacturers.
  website: https://www.noirsboxes.com
  email: ""

voice:
  tone: "technical, authoritative, solution-focused; problem-aware, not hypey"
  audience:
    - mobile repair technicians
    - cross-border e-commerce sellers (Amazon / eBay / Shopee)
    - QC / sourcing teams at electronics distributors
    - charger / cable manufacturers
    - picky iPhone power-users who want to verify their accessories
  emphasis:
    - real-world counterfeit / dead-cable detection
    - protocol identification (PD, QC, BC1.2)
    - measurable evidence (voltage / current / ripple curves on screen)
    - MFi certification + E-Marker chip verification (cables)
    - dispute reduction for sellers; OTA protocol updates
  forbidden_words:
    - guaranteed
    - cheapest
    - scam
    - fake
  forbidden_behavior:
    - competitor name-drops (specific brands like Anker, Belkin)
    - unverified claims about specific charger brands being counterfeit
    - aggressive scarcity / urgency tactics
    - mystery / occult / collectible framing

socials:
  facebook:
    url: https://www.facebook.com/BlackMagicNoirsBoxes/
    handle: BlackMagicNoirsBoxes
    page_id: ""
    asset_id: ""
  instagram:
    url: https://www.instagram.com/black_magic_noirsboxes/
    handle: black_magic_noirsboxes
  x:
    url: https://x.com/NoirsBoxes
    handle: NoirsBoxes
  threads:
    url: https://www.threads.net/@black_magic_noirsboxes
    handle: black_magic_noirsboxes
  youtube:
    url: https://www.youtube.com/@boxesnoirs
    handle: boxesnoirs
  tiktok:
    url: https://www.tiktok.com/@noirs.boxes
    handle: noirs.boxes

storefronts:
  amazon_md903: https://www.amazon.com/dp/B0DZBZ9W55
  amazon_md905: https://www.amazon.com/Noirsboxes-Charging-Certification-Portable-Lightning/dp/B0DZBSFV71
  official: https://www.noirsboxes.com
  taobao: https://shop401155113.world.taobao.com/
  rakuten: https://item.rakuten.co.jp/twdirect/c/0000002065/

products:
  - id: md-903
    sku: MD-903
    name: "MD-903 Charger / Adapter Tester"
    color: red
    category: charger-adapter-tester
    url: https://www.amazon.com/dp/B0DZBZ9W55
    selling_points:
      - detects PD / QC fast-charge protocols
      - real-time voltage / current / power readout on 3" TFT
      - ripple noise + rise/fall time analysis
      - 1020 mAh battery; 115g portable
      - OTA firmware updates as new protocols emerge
    target_audience: [repair shops, e-commerce sellers, picky iPhone users]
    suggested_themes: [counterfeit charger demo, PD vs QC explainer, before/after dispute story, lab readout close-up]

  - id: md-905
    sku: MD-905
    name: "MD-905 Charging Cable Tester"
    color: black
    category: cable-tester
    url: https://www.amazon.com/Noirsboxes-Charging-Certification-Portable-Lightning/dp/B0DZBSFV71
    selling_points:
      - detects MFi (Made for iPhone) certification
      - reads E-Marker chip on data cables
      - measures voltage / power output through the cable
      - portable digital display, Lightning compatible
    target_audience: [repair shops, mobile accessories sellers, QC teams]
    suggested_themes: [MFi check demo, E-Marker reveal, dead-cable autopsy, fake-vs-real side-by-side]

content_themes:
  - real-world counterfeit detection demo
  - protocol explainer (PD / QC / BC1.2)
  - lab readout close-up (TFT display showing live measurement)
  - dispute reduction story for sellers
  - MFi / E-Marker reveal
  - dead-cable autopsy
  - OTA firmware update reveal

content_style:
  facebook:  { caption_length: medium, hashtag_count: 3, link_policy: og_card,  notes: "lead with 'have you ever bought a fake charger' style hook" }
  instagram: { caption_length: medium, hashtag_count: 8, link_policy: bio_only, notes: "first frame = TFT screen close-up; carousel for before/after readings" }
  x:         { caption_length: short,  hashtag_count: 2, link_policy: inline,   notes: "<=280 chars; lead with the surprising reading" }
  threads:   { caption_length: medium, hashtag_count: 1, link_policy: inline,   notes: "conversational repair-shop voice" }
  youtube:   { caption_length: long,   hashtag_count: 8, link_policy: inline,   notes: "SEO terms: PD tester, MFi checker, fake charger detector" }
  tiktok:    { caption_length: short,  hashtag_count: 5, link_policy: bio_only, notes: "trending repair / tech-debunk format" }

competitor_products:
  - name: "ChargerLAB POWER-Z"
    similar_to: md-903
    category: usb-pd-tester
    region: cn / global
    socials:
      facebook:  https://www.facebook.com/chargerlab/
      instagram: https://www.instagram.com/chargerlabs/
      x:         https://x.com/chargerlab
      youtube:   https://www.youtube.com/channel/UCbHlweun5NkTVDGmeqGmwjA
      tiktok:    https://www.tiktok.com/@chargerlab
      threads:   ""
    notes: "shared social handles with CT001 entry; scrape de-duplicates"

  - name: "ChargerLAB POWER-Z CT001"
    similar_to: md-905
    category: cable-tester
    region: cn / global
    socials:
      facebook:  https://www.facebook.com/chargerlab/
      instagram: https://www.instagram.com/chargerlabs/
      x:         https://x.com/chargerlab
      youtube:   https://www.youtube.com/channel/UCbHlweun5NkTVDGmeqGmwjA
      tiktok:    https://www.tiktok.com/@chargerlab
      threads:   ""
    notes: "same brand as POWER-Z; cable-side product line"

  - name: "Total Phase Advanced Cable Tester v2"
    similar_to: md-905
    category: cable-tester
    region: us
    socials:
      facebook:  https://www.facebook.com/totalphase/
      instagram: ""
      x:         https://x.com/totalphase
      youtube:   ""
      tiktok:    ""
      threads:   ""
    notes: "B2B-leaning; low social activity outside FB/X"

reference_urls:
  own:
    - https://www.facebook.com/BlackMagicNoirsBoxes/
    - https://www.instagram.com/black_magic_noirsboxes/
    - https://x.com/NoirsBoxes
    - https://www.tiktok.com/@noirs.boxes
    - https://www.youtube.com/@boxesnoirs
  competitors: []

media_library:
  assets_dir: media/assets/noirs-boxes
  inbox_dir: media/assets/noirs-boxes/inbox
  hints:
    - "clean product shot on neutral / dark surface; brand colors = black + red"
    - "TFT display close-up showing real readings (voltage / current numbers)"
    - "lab desk environment; oscilloscope / cable / charger as props"
    - "before-after side-by-side for fake-vs-real demos"
    - "avoid mystery / occult / collectible framing"

storage:
  drafts_dir: reports/drafts/noirs-boxes
  posts_dir: reports/posts/noirs-boxes
  plans_dir: reports/plans/noirs-boxes
```

- [ ] **Step 2: Validate it parses**

Run:
```bash
node -e 'import("yaml").then(({default:y})=>import("node:fs").then(f=>{const d=y.parse(f.readFileSync("config/brands/noirs-boxes.yaml","utf8"));console.log("brand:",d.brand.slug,"products:",d.products.map(p=>p.id).join(","),"competitors:",d.competitor_products.length)}))'
```

Expected output:
```
brand: noirs-boxes products: md-903,md-905 competitors: 3
```

(If `yaml` is not installed yet, run `npm install yaml` first — it will be needed by the orchestrator anyway.)

- [ ] **Step 3: Commit**

```bash
git add config/brands/noirs-boxes.yaml package.json package-lock.json
git commit -m "feat(brand): rewrite noirs-boxes YAML to charger/cable tester voice + lock competitor_products[]"
```

---

## Task 2: Update plan-export.mjs to emit 6 sheets

**Files:**
- Modify: `scripts/plan-export.mjs`
- Create: `tests/plan-export.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `tests/plan-export.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import ExcelJS from "exceljs";

test("plan-export emits 6 sheets with TopicResearch + OwnHistory", async () => {
  const dir = mkdtempSync(join(tmpdir(), "plan-export-"));
  const planPath = join(dir, "plan.json");
  writeFileSync(
    planPath,
    JSON.stringify({
      meta: { brand: "noirs-boxes", iso_week: "2026-W19", generated_at: "2026-05-10T00:00:00Z", model: "claude-opus-4-7" },
      schedule: [{ slot_id: "2026-W19-ig-mon-1230", weekday: "Mon", time_local: "12:30", platform: "instagram", mode: "post", theme: "MFi check demo", product_id: "md-905", caption: "...", hashtags: ["#mfi"], media_path: "x.jpg", reference_urls: [], status: "planned", posted_url: "", posted_at: "", draft_id: "weekly-2026-W19-ig-mon-1230" }],
      frequency: [{ platform: "instagram", posts_per_week: 4, preferred_weekdays: ["Mon"], preferred_times: ["12:30"], rationale: "test" }],
      topic_research: [{ platform: "instagram", competitor_product: "ChargerLAB POWER-Z", similar_to: "md-903", relevant_to: "md-903", post_url: "https://...", posted_at: "2026-04-01", likes: 100, comments: 5, shares: 0, views: 1000, hook: "test hook", tone: "technical-demo", layout: "video + caption", why_it_resonated: "shows real protocol", takeaway_for_us: "use TFT readouts" }],
      own_history: [{ platform: "instagram", post_url: "https://...", posted_at: "2026-04-15", likes: 50, comments: 3, shares: 0, views: 500, caption_excerpt: "PD test", tone: "technical", layout: "reel", hook: "Did you know", why_it_resonated: "specific reading", repeatable_pattern: "lead with the number" }],
      metrics: []
    })
  );

  execFileSync("node", ["scripts/plan-export.mjs", planPath], { stdio: "inherit" });

  const xlsxPath = join(dir, "2026-W19-0504-0510.xlsx");
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(xlsxPath);
  const names = wb.worksheets.map((w) => w.name);
  assert.deepEqual(names, ["TopicResearch", "OwnHistory", "Frequency", "Schedule", "Metrics", "Meta"]);

  const tr = wb.getWorksheet("TopicResearch");
  const trHeader = tr.getRow(1).values.slice(1);
  assert.deepEqual(trHeader, ["platform", "competitor_product", "similar_to", "relevant_to", "post_url", "posted_at", "likes", "comments", "shares", "views", "hook", "tone", "layout", "why_it_resonated", "takeaway_for_us"]);
  assert.equal(tr.getCell("B2").value, "ChargerLAB POWER-Z");

  const oh = wb.getWorksheet("OwnHistory");
  const ohHeader = oh.getRow(1).values.slice(1);
  assert.deepEqual(ohHeader, ["platform", "post_url", "posted_at", "likes", "comments", "shares", "views", "caption_excerpt", "tone", "layout", "hook", "why_it_resonated", "repeatable_pattern"]);
});
```

- [ ] **Step 2: Run test, verify it fails**

```bash
node --test tests/plan-export.test.mjs
```

Expected: FAIL — current plan-export emits 5 sheets including `Research`, not 6 with split sheets. Specifically the `assert.deepEqual(names, ...)` will fail.

- [ ] **Step 3: Update `scripts/plan-export.mjs`**

Replace the `addSheet("Research", ...)` block (currently lines 96–113) with two `addSheet` calls. Insert them at the **top** of the sheet sequence (before Schedule), so the order matches the test:

```js
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
```

Then move the existing `Schedule`, `Frequency`, `Metrics`, `Meta` blocks after these. Final sheet order: `TopicResearch, OwnHistory, Frequency, Schedule, Metrics, Meta`.

Also bump the file's top comment from "5 sheets" to "6 sheets":
```js
// plan.json -> plan.xlsx (6 sheets: TopicResearch, OwnHistory, Frequency, Schedule, Metrics, Meta).
```

- [ ] **Step 4: Run test, verify it passes**

```bash
node --test tests/plan-export.test.mjs
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/plan-export.mjs tests/plan-export.test.mjs
git commit -m "feat(plan-export): split Research sheet into TopicResearch + OwnHistory"
```

---

## Task 3: Install Playwright + npm scripts

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install playwright (npm package)**

```bash
npm install playwright
```

Expected: `package.json` gains `"playwright": "^1.x.y"` under `dependencies`.

- [ ] **Step 2: Install chromium browser binary**

```bash
npx playwright install chromium
```

Expected: prints download progress; ends without error. (~150 MB download.)

- [ ] **Step 3: Add npm scripts**

In `package.json`, replace the `scripts` block with:

```json
"scripts": {
  "plan-export": "node scripts/plan-export.mjs",
  "plan-import": "node scripts/plan-import.mjs",
  "action-log": "node scripts/action-log-summarize.mjs",
  "scrape:top": "node scripts/scrape-top-posts.mjs",
  "test": "node --test tests/"
}
```

- [ ] **Step 4: Smoke test the test runner**

```bash
npm test
```

Expected: runs `tests/plan-export.test.mjs` from Task 2; passes.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add playwright dep + scrape:top + test npm scripts"
```

---

## Task 4: Scaffold `scripts/scrape-top-posts.mjs` CLI + shared utils

**Files:**
- Create: `scripts/scrape-top-posts.mjs`
- Create: `scripts/scrapers/_shared.mjs`
- Create: `tests/scrape-cli.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `tests/scrape-cli.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

test("scrape-top-posts errors on missing --platform", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err, "expected non-zero exit");
  const stderr = err.stderr.toString();
  assert.match(stderr, /--platform required/);
});

test("scrape-top-posts errors on unknown platform", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs", "--platform", "myspace", "--account-url", "https://x", "--out", "/tmp/x.json"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err);
  assert.match(err.stderr.toString(), /unknown platform: myspace/);
});

test("scrape-top-posts errors on missing --account-url", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs", "--platform", "instagram", "--out", "/tmp/x.json"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err);
  assert.match(err.stderr.toString(), /--account-url required/);
});
```

- [ ] **Step 2: Run test, verify it fails**

```bash
node --test tests/scrape-cli.test.mjs
```

Expected: FAIL — file does not exist.

- [ ] **Step 3: Create the shared module**

Create `scripts/scrapers/_shared.mjs`:

```js
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
```

- [ ] **Step 4: Create the CLI entry point**

Create `scripts/scrape-top-posts.mjs`:

```js
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
```

- [ ] **Step 5: Run test, verify PASS**

```bash
node --test tests/scrape-cli.test.mjs
```

Expected: all 3 tests pass. The `unknown platform: myspace` test passes because the `SUPPORTED.includes(...)` check exits 2 before the dynamic `import(...)` is attempted.

- [ ] **Step 6: Commit**

```bash
git add scripts/scrape-top-posts.mjs scripts/scrapers/_shared.mjs tests/scrape-cli.test.mjs
git commit -m "feat(scrape): scaffold scrape-top-posts CLI + shared utils"
```

---

## Task 5: Implement Instagram scraper module

**Files:**
- Create: `scripts/scrapers/instagram.mjs`
- Create: `tests/scraper-instagram-parse.test.mjs`
- Create: `tests/fixtures/instagram-feed.html`

- [ ] **Step 1: Create the fixture**

Save a minimal IG profile feed HTML stub to `tests/fixtures/instagram-feed.html`. Use the structure IG returns server-side for a public profile (article tags wrap each post; `aria-label` carries like/comment counts). Real IG markup changes; this fixture only needs to exercise our parser, so synthesize plausible markup:

```html
<!doctype html>
<html><body>
<main>
  <article>
    <a href="/p/AAA111/" role="link"><img src="thumb1.jpg" alt="post 1"/></a>
    <span aria-label="1,234 likes">1,234 likes</span>
    <span aria-label="45 comments">45 comments</span>
    <time datetime="2026-04-22T12:00:00Z"></time>
    <div data-caption>Lab readout: PD 65W tested</div>
  </article>
  <article>
    <a href="/p/BBB222/" role="link"><img src="thumb2.jpg" alt="post 2"/></a>
    <span aria-label="89 likes">89 likes</span>
    <span aria-label="2 comments">2 comments</span>
    <time datetime="2026-04-20T08:00:00Z"></time>
    <div data-caption>Cable autopsy day</div>
  </article>
  <article>
    <a href="/reel/CCC333/" role="link"><img src="thumb3.jpg" alt="reel 1"/></a>
    <span aria-label="5,678 views">5,678 views</span>
    <span aria-label="412 likes">412 likes</span>
    <span aria-label="33 comments">33 comments</span>
    <time datetime="2026-04-18T20:00:00Z"></time>
    <div data-caption>MFi check in 30 seconds</div>
  </article>
</main>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-instagram-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseFeed } from "../scripts/scrapers/instagram.mjs";

test("parseFeed extracts post_url, type, likes, comments, views, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/instagram-feed.html", "utf8");
  const posts = parseFeed(html, "https://www.instagram.com/black_magic_noirsboxes/");
  assert.equal(posts.length, 3);

  assert.deepEqual(posts[0], {
    post_url: "https://www.instagram.com/p/AAA111/",
    media_type: "image",
    likes: 1234,
    comments: 45,
    views: null,
    posted_at: "2026-04-22T12:00:00Z",
    caption: "Lab readout: PD 65W tested",
    thumbnail_url: "thumb1.jpg",
    hashtags: []
  });

  assert.equal(posts[2].media_type, "reel");
  assert.equal(posts[2].views, 5678);
  assert.equal(posts[2].likes, 412);
});

test("parseFeed sorts by engagement descending when ranked", async () => {
  const { rankByEngagement } = await import("../scripts/scrapers/instagram.mjs");
  const ranked = rankByEngagement([
    { likes: 10, comments: 1, views: 0 },
    { likes: 1000, comments: 50, views: 0 },
    { likes: 100, comments: 5, views: 0 }
  ]);
  assert.equal(ranked[0].likes, 1000);
  assert.equal(ranked[1].likes, 100);
  assert.equal(ranked[2].likes, 10);
});
```

- [ ] **Step 3: Run, verify FAIL**

```bash
node --test tests/scraper-instagram-parse.test.mjs
```

Expected: FAIL — module does not exist.

- [ ] **Step 4: Implement the Instagram module**

Create `scripts/scrapers/instagram.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

const RE_NUM = /([\d,]+)\s+(likes|comments|views)/i;

function num(text) {
  const m = RE_NUM.exec(text || "");
  return m ? Number(m[1].replace(/,/g, "")) : null;
}

function attr(html, tag, attrName) {
  const re = new RegExp(`<${tag}[^>]*\\s${attrName}="([^"]*)"`, "i");
  const m = re.exec(html);
  return m ? m[1] : null;
}

export function parseFeed(html, baseUrl) {
  const articles = html.split(/<article[\s>]/i).slice(1);
  const out = [];
  for (const block of articles) {
    const article = "<article " + block.split(/<\/article>/i)[0];
    const href = attr(article, "a", "href");
    if (!href) continue;
    const post_url = href.startsWith("http") ? href : new URL(href, baseUrl).toString();
    const media_type = href.includes("/reel/") ? "reel" : "image";
    const likesM = /aria-label="([^"]*\blikes\b[^"]*)"/i.exec(article);
    const commentsM = /aria-label="([^"]*\bcomments\b[^"]*)"/i.exec(article);
    const viewsM = /aria-label="([^"]*\bviews\b[^"]*)"/i.exec(article);
    const time = attr(article, "time", "datetime");
    const captionM = /<div[^>]*data-caption[^>]*>([^<]*)<\/div>/i.exec(article);
    const thumb = attr(article, "img", "src");
    const caption = captionM ? captionM[1].trim() : "";
    const hashtags = (caption.match(/#\w+/g) || []);
    out.push({
      post_url,
      media_type,
      likes: likesM ? num(likesM[1]) : null,
      comments: commentsM ? num(commentsM[1]) : null,
      views: viewsM ? num(viewsM[1]) : null,
      posted_at: time,
      caption,
      thumbnail_url: thumb,
      hashtags
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  const score = (p) => (p.likes || 0) + 3 * (p.comments || 0) + 0.1 * (p.views || 0);
  return [...posts].sort((a, b) => score(b) - score(a));
}

async function scrollFor(page, batches, runId) {
  for (let i = 0; i < batches; i++) {
    await page.evaluate(() => window.scrollBy(0, window.innerHeight * 2));
    await jitter(400, 1200);
    appendScrapeLog(runId, "instagram", { event: "scroll-batch", batch: i });
  }
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    appendScrapeLog(runId, "instagram", { event: "navigate", url: accountUrl });
    await page.goto(accountUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(800, 1500);

    if (page.url().includes("/accounts/login")) {
      throw new Error("login_wall");
    }

    const batches = Math.ceil(recent / 12);
    await scrollFor(page, batches, runId);

    const html = await page.content();
    const posts = parseFeed(html, accountUrl);
    appendScrapeLog(runId, "instagram", { event: "parsed", count: posts.length });

    const ranked = rankByEngagement(posts).slice(0, top);
    return {
      platform: "instagram",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: ranked
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-instagram-parse.test.mjs
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/instagram.mjs tests/scraper-instagram-parse.test.mjs tests/fixtures/instagram-feed.html
git commit -m "feat(scrape): instagram scraper with parse + rank tests"
```

---

## Task 6: Live smoke test — Instagram against own account

**Files:** none modified

- [ ] **Step 1: Confirm logged-in profile exists**

```bash
ls browser_profiles/noirs-boxes/ 2>/dev/null && echo OK || echo MISSING
```

Expected: `OK`. If `MISSING`, the user must run `/first-time-login` first. Stop and surface this; do not proceed.

- [ ] **Step 2: Run scraper against own IG**

```bash
node scripts/scrape-top-posts.mjs \
  --brand noirs-boxes \
  --platform instagram \
  --account-url https://www.instagram.com/black_magic_noirsboxes/ \
  --recent 30 \
  --top 5 \
  --out /tmp/ig-smoke.json \
  --run-id smoke-$(date +%s)
```

Expected: a chromium window opens (headed), navigates, scrolls, closes. stdout prints `/tmp/ig-smoke.json`. Exit 0.

If exit non-zero: read `/tmp/ig-smoke.json` — it will contain `{ "error": "...", "step_failed": "..." }`. Common failures:
- `login_wall` → session expired. User runs `/first-time-login` and retries.
- `Timeout` → IG slow / blocked. Retry once; if still failing, surface and stop.

- [ ] **Step 3: Inspect output**

```bash
cat /tmp/ig-smoke.json | head -50
```

Expected: JSON with `platform`, `account_url`, `scraped_at`, `recent_count > 0`, `top` array of up to 5 posts with `post_url`, `media_type`, `likes`/`comments`/`views`, `posted_at`, `caption`, `hashtags`.

- [ ] **Step 4: Inspect scrape log**

```bash
ls data/scrape-logs/ | head -5
tail -20 data/scrape-logs/smoke-*-instagram.jsonl
```

Expected: a `.jsonl` file with `navigate`, `scroll-batch`, `parsed` events.

- [ ] **Step 5: Manual sanity check**

Open `top[0].post_url` in a browser. Confirm the like/comment numbers in the JSON roughly match the live page (within ±10% drift due to time gap).

If numbers are wildly off (e.g. 0 everywhere, or all the same number) — the parser is matching the wrong attribute. Pause and diagnose; do not proceed to other platforms until IG is solid.

- [ ] **Step 6: Document the smoke result**

In your task journal / commit message, note: "IG smoke OK — N posts, top likes M". No code change.

---

## Task 7: Update weekly-plan-* SKILL files

**Files:**
- Modify: `.claude/skills/weekly-plan-research/SKILL.md`
- Modify: `.claude/skills/weekly-plan-draft/SKILL.md`
- Modify: `.claude/skills/weekly-plan-schedule/SKILL.md`
- Modify: `.claude/skills/weekly-plan-export/SKILL.md`

- [ ] **Step 1: Rewrite `weekly-plan-research/SKILL.md`**

Replace the entire file with:

```markdown
---
name: weekly-plan-research
description: Per-platform top-post analysis. Own posts via Node Playwright script (logged in, real metrics). Competitor products via fetch-reference (public).
---

> Common rules: `docs/OPERATING_RULES.md`. Subagent-friendly: orchestrator spawns one of these per platform in parallel, **but** the own-post scrape step happens in the main session before subagents fan out (see Strategy below).

## Input
- `platform`: one of `facebook|instagram|x|threads|youtube|tiktok`.
- `own_account_url`: from `socials.<platform>.url` in active brand YAML.
- `own_top_json_path`: absolute path to the JSON written by `scripts/scrape-top-posts.mjs` (main session produces this before spawning the subagent).
- `competitor_products`: list of `{ name, similar_to, socials.<platform> }` from `competitor_products[]` in brand YAML, filtered to entries where `socials.<platform>` is non-empty. De-duplicated by URL.
- `lookback_days`: integer (default 14) — used for own-post analysis filtering only.

## Output (JSON)

```json
{
  "platform": "instagram",
  "researched_at": "<ISO>",
  "own_history_rows": [
    {
      "post_url": "https://...",
      "posted_at": "<ISO>",
      "media_type": "image|reel|video",
      "likes": 1234, "comments": 56, "shares": null, "views": null,
      "caption_excerpt": "first 120 chars",
      "tone": "technical-demo",
      "layout": "TFT close-up + 2-line caption + 8 hashtags",
      "hook": "first-line text",
      "why_it_resonated": "concise reason",
      "repeatable_pattern": "lead with the on-screen number"
    }
  ],
  "topic_research_rows": [
    {
      "competitor_product": "ChargerLAB POWER-Z",
      "similar_to": "md-903",
      "relevant_to": "md-903",
      "post_url": "https://...",
      "posted_at": "<ISO>",
      "likes": 1234, "comments": 56, "shares": null, "views": null,
      "tone": "technical-demo",
      "layout": "video + caption",
      "hook": "first-line text",
      "why_it_resonated": "concise reason",
      "takeaway_for_us": "one-sentence insight applicable to our SKU"
    }
  ]
}
```

## Strategy

### Own posts (script-produced, then LLM-analyzed)

The orchestrator runs `node scripts/scrape-top-posts.mjs --platform <p> --account-url <own_account_url> --top 10 --recent 60 --out <path>` in the **main session** (browser session does not propagate to subagents). It then passes the resulting JSON path to this skill running in a subagent.

In the subagent:
1. Load the JSON from `own_top_json_path`.
2. For each entry in `top[]`, fill in `tone`, `layout`, `hook`, `why_it_resonated`, `repeatable_pattern` using the `caption` and visible metrics. Truncate caption to 120 chars for `caption_excerpt`.
3. Drop entries posted before `now - lookback_days` if filtering is requested; otherwise pass through as-is.

### Competitor products (no login)

1. De-duplicate `competitor_products[].socials[<platform>]` URLs (multiple entries may share the same handle).
2. For each unique URL, spawn a `fetch-reference` subagent — orchestrator handles the spawning. This skill receives back `summary` / `key_points` / `images` per page.
3. Identify up to 3 top posts per URL (by visible engagement; if hidden, by recency).
4. For each post:
   - Set `competitor_product` to the rival entry name (or join names with " / " if multiple entries share the URL).
   - Set `similar_to` to that entry's brand-level value (or join if multiple).
   - Determine `relevant_to` from the post content itself: which of our SKUs (`md-903 | md-905 | both | neither`) does the post topically map to? Use the post's text + media to decide; do not default to `similar_to`.
5. Fill `tone`, `layout`, `hook`, `why_it_resonated`, `takeaway_for_us`.

### LLM-extract notes per row

- `tone`: short phrase (e.g. "technical-demo", "high-energy hype", "mock-academic").
- `layout`: structure description (e.g. "TFT close-up + 2-line caption + 8 hashtags").
- `hook`: first 70 chars of the post that does the work.
- `why_it_resonated`: 1 sentence; tie to emotion / utility / timing / format novelty / community-specific reference.
- `takeaway_for_us`: 1 sentence applicable to one of our SKUs. (Topic rows only.)
- `repeatable_pattern`: 1 sentence describing the pattern we could replicate. (Own rows only.)

## Don'ts

- Do not write to disk — return JSON only. Orchestrator persists to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.
- Do not scrape competitor pages with the logged-in browser session.
- Do not scrape own pages with `fetch-reference` — own pages always come through the script.
- Do not invent engagement metrics. Missing → `null`.
- Do not exceed 10 own_history_rows or 8 topic_research_rows per platform — quality over volume.
- Do not call other skills directly. The orchestrator chains everything.
```

- [ ] **Step 2: Rewrite `weekly-plan-draft/SKILL.md`**

Replace the entire file with:

```markdown
---
name: weekly-plan-draft
description: Generate caption + hashtags + media plan + product_id for one schedule slot. Subagent-friendly: orchestrator spawns one per slot in parallel.
---

> Common rules: `docs/OPERATING_RULES.md`.

## Input
- `slot`: one row from `weekly-plan-schedule.schedule[]` (slot_id, weekday, time_local, platform, mode, theme; `product_id` arrives as `null` and this skill fills it).
- `available_products`: full `products[]` from active brand YAML.
- `topic_research_rows`: subset of `topic_research_rows` filtered to this slot's platform.
- `own_history_rows`: subset of `own_history_rows` filtered to this slot's platform.
- `brand_yaml`: the active brand profile (full).
- `reference`: optional — `fetch-reference` output if the slot is news/event-driven.

## Output (JSON)

```json
{
  "slot_id": "2026-W19-ig-mon-1230",
  "platform": "instagram",
  "mode": "post",
  "product_id": "md-905",
  "caption": "...",
  "hashtags": ["#...", "#..."],
  "media_path": "media/assets/<brand>/<...>.jpg",
  "reference_urls": ["https://..."],
  "draft_id": "weekly-2026-W19-ig-mon-1230",
  "rationale": "one or two sentences on product/tone/hook choice grounded in research_rows"
}
```

`draft_id` is synthesized from `slot_id` so `/publish-from-plan` can write a normal draft JSON for tracing.

## Behavior

1. Load the matching `draft-<platform>` SKILL.md mentally — it sets the rules for length, hashtag count, link policy. Follow them.

2. **Pick `product_id`** from `available_products`:
   - For each product, score `slot.theme` against `product.suggested_themes` (substring or stem match counts). Pick the highest-scoring product.
   - If two products tie or `slot.theme` is generic, pick the product with fewer slots already assigned this week (alternation tie-break — orchestrator passes a `weekly_assignments_so_far` count if available; otherwise pick alphabetically).
   - If `available_products` is empty, set `product_id: null` and proceed.

3. **Filter research for SKU**:
   - From `topic_research_rows`, keep rows where `relevant_to == product_id` or `relevant_to == "both"`.
   - Use these + `own_history_rows` to abstract patterns (tone, opening hook style, layout) — do not lift sentences.

4. **Pick `media_path`**:
   - Look in `media/assets/<brand>/<product_id>/` for an image / video matching `mode`.
   - If nothing fits → fall back to `media/assets/<brand>/` library roots.
   - If still nothing → return `media_path: null` and add to `rationale` "needs media (orchestrator: route to image-generator)".

5. Honor `voice.forbidden_words` and `voice.forbidden_behavior` from the brand YAML.

## Don'ts

- Do not call `publish-*` or `image-generator` directly — the orchestrator does that on the back of `media_path: null`.
- Do not write files — return JSON only.
- Do not duplicate captions across slots — vary hooks even when the theme is identical.
- Do not invent engagement metrics or research data. Use what `topic_research_rows` / `own_history_rows` provide; if a slot's platform has no research data, draft conservatively from brand YAML alone and say so in `rationale`.
- Do not pick a `product_id` not present in `available_products`.
```

- [ ] **Step 3: Patch `weekly-plan-schedule/SKILL.md`**

Replace the "Theme + product assignment" section (currently around lines 70–73) with:

```markdown
## Theme + product assignment

- Pull `theme` from `content_themes[]`. Round-robin within the week so the brand does not post the same theme back-to-back on the same platform.
- Set `product_id: null`. The downstream `weekly-plan-draft` step picks the product per slot by matching `slot.theme` to each product's `suggested_themes`.
```

- [ ] **Step 4: Patch `weekly-plan-export/SKILL.md`**

Replace the "Sheet structure (handled by the script)" section with:

```markdown
## Sheet structure (handled by the script)

- `TopicResearch`: rival-product top posts with tone/hook/why analysis.
- `OwnHistory`: own-account top posts with tone/hook/why analysis + repeatable pattern.
- `Frequency`: per-platform cadence + rationale.
- `Schedule`: per-slot rows with caption / hashtags / product_id.
- `Metrics`: empty until `weekly-plan-review` populates it next week.
- `Meta`: brand, iso_week, generated_at, prev_week_plan_path, own_top_scraped_at, model, notes.
```

- [ ] **Step 5: Smoke test the SKILL files load as valid markdown**

```bash
for f in .claude/skills/weekly-plan-{research,draft,schedule,export}/SKILL.md; do
  head -3 "$f" | grep -q "^name:" && echo "$f: OK" || echo "$f: BROKEN frontmatter"
done
```

Expected: all 4 files print `OK`.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/weekly-plan-research/SKILL.md \
        .claude/skills/weekly-plan-draft/SKILL.md \
        .claude/skills/weekly-plan-schedule/SKILL.md \
        .claude/skills/weekly-plan-export/SKILL.md
git commit -m "feat(skills): wire script-based own-top + product_id selection + 6-sheet export"
```

---

## Task 8: Update `/weekly-plan` command + project docs

**Files:**
- Modify: `.claude/commands/weekly-plan.md`
- Modify: `docs/WEEKLY_PLAN.md`
- Modify: `docs/OPERATING_RULES.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Patch `/weekly-plan` command**

Replace the entire "## Steps" section in `.claude/commands/weekly-plan.md` with:

```markdown
## Steps

1. Resolve target ISO week:
   - `--week 2026-W19` → use it.
   - Default → current ISO week (`date +%G-W%V`).
2. Resolve active brand (`BRAND` env → `config/active-brand`).
3. Make `reports/plans/<brand>/<iso_week>/research/` if missing.
4. Generate run id (`YYYYMMDD-HHMMSS-<rand4>`); set `meta.mode = "weekly-plan"`.

5. **Last-week metrics (MCP)** — only if a previous plan exists at `reports/plans/<brand>/<prev iso_week>/plan.json` with at least one `Schedule.posted_url`:
   - Read `.claude/skills/weekly-plan-review/SKILL.md`.
   - Main session runs the Playwright MCP scrape (logged-in, own posts only). Wrap each MCP call in the action log.
   - Updates `prev plan.json` (Metrics sheet) and `data/stats-history/<brand>.json`.
   - Re-exports the previous week's xlsx via `weekly-plan-export`.
   - **`browser_close` when done — required before step 6.**

6. **Own-top scrape (script, sequential)**:
   - For each platform in `socials[]`:
     - Run: `node scripts/scrape-top-posts.mjs --brand <slug> --platform <p> --account-url <socials.p.url> --recent 60 --top 10 --out reports/plans/<brand>/<iso_week>/research/own-<p>-top.json --run-id <run_id>`.
     - On non-zero exit, the script writes a structured error JSON to the `--out` path. Capture it; surface to the user but continue with other platforms.
   - All scrape calls are sequential (single chromium, shared profile).

7. **Research per platform** (subagents, parallel — one per platform):
   - For each platform spawn `subagent_type: general-purpose`:
     - Prompt: "Read `.claude/skills/weekly-plan-research/SKILL.md`. Inputs: `own_top_json_path = reports/plans/<brand>/<iso_week>/research/own-<p>-top.json`; `competitor_products` filtered to entries with `socials.<p>` non-empty (de-duplicated by URL); spawn `fetch-reference` subagents per unique competitor URL. Return JSON exactly per SKILL.md output."
   - Persist each platform's research to `reports/plans/<brand>/<iso_week>/research/<platform>.json`.

8. **Schedule** (main session, no subagent — pure compute):
   - Read `.claude/skills/weekly-plan-schedule/SKILL.md`.
   - Inputs: aggregated research, `prev_metrics` (if step 5 ran), brand `content_style`.
   - Output: `frequency[]` + `schedule[]` (each `slot.product_id = null`).

9. **Drafts** (subagents, parallel — one per slot):
   - For each `slot` in `schedule[]`, spawn one `weekly-plan-draft` subagent.
   - Pass: `slot`, `available_products` (full `brand.products[]`), `topic_research_rows` filtered to that platform, `own_history_rows` filtered to that platform, `brand_yaml`, `reference` (if applicable).
   - Subagent prompt: "Read `.claude/skills/weekly-plan-draft/SKILL.md`. Pick product_id by theme fit. Return JSON exactly per output schema."
   - Aggregate all draft results back into `schedule[]` rows (caption, hashtags, media_path, reference_urls, draft_id, rationale, product_id).

10. **Compose `plan.json`**:

    ```json
    {
      "schedule": [...],
      "frequency": [...],
      "topic_research": [...],
      "own_history": [...],
      "metrics": [],
      "meta": {
        "brand": "<slug>",
        "iso_week": "<YYYY-Www>",
        "generated_at": "<ISO>",
        "prev_week_plan_path": "<path or null>",
        "own_top_scraped_at": "<ISO>",
        "model": "claude-opus-4-7",
        "notes": ""
      }
    }
    ```

    Write to `reports/plans/<brand>/<iso_week>/plan.json`.

11. **Export xlsx**: invoke `weekly-plan-export` with the json path. Verify file exists.

12. **Reply** (channel: TG `reply`; terminal: main-session text). Plain text:

    ```
    📅 weekly plan <iso_week>
    schedule: 22 slots across 6 platforms
    facebook: 3 posts (Tue Thu Sat 11:00 / 19:00)
    instagram: 4 posts (Mon Wed Fri Sun 12:30 / 20:00)
    ...

    plan.json: reports/plans/<brand>/<iso_week>/plan.json
    plan.xlsx: reports/plans/<brand>/<iso_week>/<iso_week>-MMDD-MMDD.xlsx

    own-top scraped: 6/6 platforms
    last week's metrics: <updated | none>

    review the plan, then run /publish-from-plan --day today.
    ```
```

Also replace the "## Verification" section with:

```markdown
## Verification

- [ ] `reports/plans/<brand>/<iso_week>/plan.json` and the matching `.xlsx` exist.
- [ ] `Schedule` has at least one slot per requested platform; every slot has a non-null `product_id` (when `brand.products[]` is non-empty).
- [ ] `OwnHistory` has rows for at least one platform (script ran successfully).
- [ ] `TopicResearch` has rows for at least the platforms with reachable competitor accounts (FB, X for v1).
- [ ] If a previous-week plan existed, its `Metrics` sheet has fresh rows.
- [ ] Action log written for MCP review step. Scrape logs written for each own-top scrape under `data/scrape-logs/`.
```

- [ ] **Step 2: Patch `docs/WEEKLY_PLAN.md`**

In the "Sheet reference" section, replace the `### Research` subsection with:

```markdown
### TopicResearch

Rival-product top-post analysis. One row per (competitor_product × post). Columns: `platform, competitor_product, similar_to, relevant_to, post_url, posted_at, likes, comments, shares, views, hook, tone, layout, why_it_resonated, takeaway_for_us`.

`similar_to` = the brand-level hint from YAML (which of our SKUs the rival generally competes with). `relevant_to` = LLM's per-post determination (could be different from `similar_to` because a single competitor account posts about multiple products).

### OwnHistory

NoirsBoxes own-account top posts, scraped weekly via `scripts/scrape-top-posts.mjs`. Columns: `platform, post_url, posted_at, likes, comments, shares, views, caption_excerpt, tone, layout, hook, why_it_resonated, repeatable_pattern`.

Top 10 per platform from the most recent ~60 posts, ranked by engagement.
```

In the "## Files per week" tree, change:

```
└── research/
    ├── facebook.json
    ├── instagram.json
    ├── x.json
    ├── threads.json
    ├── youtube.json
    └── tiktok.json
```

to:

```
└── research/
    ├── own-{facebook,instagram,x,threads,youtube,tiktok}-top.json   # raw script output
    ├── {facebook,instagram,x,threads,youtube,tiktok}.json           # LLM-analyzed (own + topic)
```

In the "## Generation pipeline" section, change step 2 to mention the script:

```markdown
2. **Own-top scrape** (main session, sequential):
   - `scripts/scrape-top-posts.mjs` runs once per platform against the brand's logged-in profile. Writes `research/own-<platform>-top.json`.

3. **Research per platform** (parallel):
   - One `weekly-plan-research` subagent per platform.
   - Subagent reads the own-top JSON for analysis; gathers competitor URLs via `fetch-reference`.
   - Per-platform output saved as `research/<platform>.json`.
```

(Renumber subsequent steps accordingly: schedule becomes 4, drafts 5, compose 6.)

- [ ] **Step 3: Add §11 to `docs/OPERATING_RULES.md`**

Append to the file (after §10):

```markdown
## 11. Playwright tool split

- **Writes** (publish, delete, login) → Playwright **MCP**. Action log wraps every `mcp__playwright__browser_*` call.
- **Bulk read scraping** (own-account top posts) → Node script under `scripts/scrape-*.mjs`. Independent log under `data/scrape-logs/<run-id>-<platform>.jsonl`.
- **Competitor read** → `fetch-reference` (WebFetch) — best-effort, no logged-in session. Treats login walls as expected and returns sparse data.
- MCP and the Node script **must not share** `browser_profiles/<brand>/` concurrently. Orchestrator serializes: MCP step ends with `browser_close` before any script step begins.
- Profile lock conflict → `{ "error": "profile lock conflict, run /unlock-browser..." }` per §9.
```

- [ ] **Step 4: Patch `CLAUDE.md`**

In the "Don't list" section, the existing bullet `- Don't take screenshots to disk except on error (action path).` stays. Add a new section after it:

```markdown
## Playwright split (see OPERATING_RULES §11)

- Writes → MCP. Reads (bulk own-account scraping) → `scripts/scrape-*.mjs`. Profile dir is shared, never concurrent.
- Scrape script writes `data/scrape-logs/<run-id>-<platform>.jsonl`. Action log stays MCP-only.
```

- [ ] **Step 5: Sanity check**

```bash
grep -l "competitors\[\]" .claude/skills/ docs/ -r 2>/dev/null
```

Expected: no matches (all references to the old `competitors[]` field have been migrated to `competitor_products[]`). If any matches appear, update them.

- [ ] **Step 6: Commit**

```bash
git add .claude/commands/weekly-plan.md docs/WEEKLY_PLAN.md docs/OPERATING_RULES.md CLAUDE.md
git commit -m "feat(orchestrator): wire 12-step weekly-plan with script-based own-top scrape"
```

---

## Task 9: Implement Facebook scraper module

**Files:**
- Create: `scripts/scrapers/facebook.mjs`
- Create: `tests/fixtures/facebook-page.html`
- Create: `tests/scraper-facebook-parse.test.mjs`

- [ ] **Step 1: Create the fixture**

Save a minimal FB Page HTML stub to `tests/fixtures/facebook-page.html`. FB Page server-rendered markup uses `[data-pagelet]` and `[role=article]` containers; engagement counts live in `<span>` next to like/comment SVG icons. Synthesize plausible markup matching the parser's contract:

```html
<!doctype html>
<html><body>
<div role="main">
  <div role="article">
    <a href="/BlackMagicNoirsBoxes/posts/1111111111111" aria-label="Permalink to post">post 1</a>
    <abbr data-utime="1714000000">22 April</abbr>
    <span aria-label="234 reactions">234</span>
    <span aria-label="12 comments">12</span>
    <span aria-label="5 shares">5</span>
    <div data-ad-comet-preview="message">Lab readout: PD 65W tested</div>
  </div>
  <div role="article">
    <a href="/BlackMagicNoirsBoxes/videos/2222222222222" aria-label="Permalink to video">video 1</a>
    <abbr data-utime="1713800000">20 April</abbr>
    <span aria-label="1.2K reactions">1.2K</span>
    <span aria-label="89 comments">89</span>
    <span aria-label="34 shares">34</span>
    <div data-ad-comet-preview="message">MFi check in 30 seconds</div>
  </div>
</div>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-facebook-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parsePage } from "../scripts/scrapers/facebook.mjs";

test("parsePage extracts post_url, type, likes, comments, shares, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/facebook-page.html", "utf8");
  const posts = parsePage(html, "https://www.facebook.com/BlackMagicNoirsBoxes/");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.facebook.com/BlackMagicNoirsBoxes/posts/1111111111111");
  assert.equal(posts[0].media_type, "post");
  assert.equal(posts[0].likes, 234);
  assert.equal(posts[0].comments, 12);
  assert.equal(posts[0].shares, 5);
  assert.equal(posts[0].caption, "Lab readout: PD 65W tested");

  assert.equal(posts[1].media_type, "video");
  assert.equal(posts[1].likes, 1200); // "1.2K"
});
```

- [ ] **Step 3: Run, verify FAIL**

```bash
node --test tests/scraper-facebook-parse.test.mjs
```

Expected: FAIL — module does not exist.

- [ ] **Step 4: Implement Facebook module**

Create `scripts/scrapers/facebook.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

function parseCount(text) {
  if (!text) return null;
  const m = /([\d.,]+)\s*([KkMm]?)/.exec(text);
  if (!m) return null;
  let n = Number(m[1].replace(/,/g, ""));
  if (m[2] === "K" || m[2] === "k") n *= 1000;
  if (m[2] === "M" || m[2] === "m") n *= 1_000_000;
  return Math.round(n);
}

function pickAriaLabel(block, keyword) {
  const re = new RegExp(`aria-label="([^"]*\\b${keyword}\\b[^"]*)"`, "i");
  const m = re.exec(block);
  return m ? m[1] : null;
}

export function parsePage(html, baseUrl) {
  const articles = html.split(/<div\s+role="article">/i).slice(1);
  const out = [];
  for (const block of articles) {
    const article = '<div role="article">' + block.split(/<\/div>\s*<div\s+role="article">/i)[0];
    const hrefM = /<a\s+href="([^"]+)"[^>]*aria-label="Permalink to (post|video|photo)"/i.exec(article);
    if (!hrefM) continue;
    const href = hrefM[1];
    const post_url = href.startsWith("http") ? href : new URL(href, baseUrl).toString();
    const utimeM = /data-utime="(\d+)"/i.exec(article);
    const captionM = /data-ad-comet-preview="message"[^>]*>([^<]*)/i.exec(article);
    out.push({
      post_url,
      media_type: hrefM[2],
      likes: parseCount(pickAriaLabel(article, "reactions")),
      comments: parseCount(pickAriaLabel(article, "comments")),
      shares: parseCount(pickAriaLabel(article, "shares")),
      views: null,
      posted_at: utimeM ? new Date(Number(utimeM[1]) * 1000).toISOString() : null,
      caption: captionM ? captionM[1].trim() : "",
      thumbnail_url: null,
      hashtags: (captionM ? captionM[1] : "").match(/#\w+/g) || []
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  const score = (p) => (p.likes || 0) + 3 * (p.comments || 0) + 5 * (p.shares || 0);
  return [...posts].sort((a, b) => score(b) - score(a));
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    appendScrapeLog(runId, "facebook", { event: "navigate", url: accountUrl });
    await page.goto(accountUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(800, 1500);

    if (page.url().includes("/login")) throw new Error("login_wall");

    const batches = Math.ceil(recent / 8);
    for (let i = 0; i < batches; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 2));
      await jitter(500, 1300);
      appendScrapeLog(runId, "facebook", { event: "scroll-batch", batch: i });
    }

    const html = await page.content();
    const posts = parsePage(html, accountUrl);
    appendScrapeLog(runId, "facebook", { event: "parsed", count: posts.length });

    return {
      platform: "facebook",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: rankByEngagement(posts).slice(0, top)
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-facebook-parse.test.mjs
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/facebook.mjs tests/scraper-facebook-parse.test.mjs tests/fixtures/facebook-page.html
git commit -m "feat(scrape): facebook scraper with parse test"
```

---

## Task 10: Implement X scraper module

**Files:**
- Create: `scripts/scrapers/x.mjs`
- Create: `tests/fixtures/x-profile.html`
- Create: `tests/scraper-x-parse.test.mjs`

- [ ] **Step 1: Create the fixture**

Save to `tests/fixtures/x-profile.html`. X uses `<article data-testid="tweet">` containers with `[data-testid=like|reply|retweet|bookmark]` for interaction counts:

```html
<!doctype html>
<html><body>
<main>
  <article data-testid="tweet">
    <a href="/NoirsBoxes/status/1111111111111111111"><time datetime="2026-04-22T12:00:00Z"></time></a>
    <div data-testid="tweetText">PD 65W tested — readout below.</div>
    <div data-testid="reply" aria-label="12 replies">12</div>
    <div data-testid="retweet" aria-label="34 reposts">34</div>
    <div data-testid="like" aria-label="567 likes">567</div>
    <a aria-label="2.3K views" href="/NoirsBoxes/status/1111111111111111111/analytics">2.3K</a>
  </article>
  <article data-testid="tweet">
    <a href="/NoirsBoxes/status/2222222222222222222"><time datetime="2026-04-20T08:00:00Z"></time></a>
    <div data-testid="tweetText">MFi check in 30s.</div>
    <div data-testid="reply" aria-label="3 replies">3</div>
    <div data-testid="retweet" aria-label="5 reposts">5</div>
    <div data-testid="like" aria-label="89 likes">89</div>
  </article>
</main>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-x-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseTimeline } from "../scripts/scrapers/x.mjs";

test("parseTimeline extracts post_url, likes, replies, reposts, views, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/x-profile.html", "utf8");
  const posts = parseTimeline(html, "https://x.com/NoirsBoxes");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://x.com/NoirsBoxes/status/1111111111111111111");
  assert.equal(posts[0].likes, 567);
  assert.equal(posts[0].comments, 12);
  assert.equal(posts[0].shares, 34);
  assert.equal(posts[0].views, 2300);
  assert.equal(posts[0].caption, "PD 65W tested — readout below.");

  assert.equal(posts[1].views, null);
});
```

- [ ] **Step 3: Run, verify FAIL**

```bash
node --test tests/scraper-x-parse.test.mjs
```

- [ ] **Step 4: Implement X module**

Create `scripts/scrapers/x.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

function parseCount(text) {
  if (!text) return null;
  const m = /([\d.,]+)\s*([KkMm]?)/.exec(text);
  if (!m) return null;
  let n = Number(m[1].replace(/,/g, ""));
  if (m[2] === "K" || m[2] === "k") n *= 1000;
  if (m[2] === "M" || m[2] === "m") n *= 1_000_000;
  return Math.round(n);
}

function pickAriaLabel(block, regex) {
  const re = new RegExp(`aria-label="(${regex.source})"`, "i");
  const m = re.exec(block);
  return m ? m[1] : null;
}

export function parseTimeline(html, baseUrl) {
  const tweets = html.split(/<article\s+data-testid="tweet">/i).slice(1);
  const out = [];
  for (const block of tweets) {
    const article = '<article data-testid="tweet">' + block.split(/<\/article>/i)[0];
    const hrefM = /<a\s+href="(\/[^"]+\/status\/\d+)"/i.exec(article);
    if (!hrefM) continue;
    const post_url = new URL(hrefM[1], baseUrl).toString();
    const timeM = /<time\s+datetime="([^"]+)"/i.exec(article);
    const captionM = /data-testid="tweetText"[^>]*>([^<]*)/i.exec(article);
    out.push({
      post_url,
      media_type: "post",
      likes: parseCount(pickAriaLabel(article, /[\d.KMkm]+\s+likes/)),
      comments: parseCount(pickAriaLabel(article, /[\d.KMkm]+\s+replies/)),
      shares: parseCount(pickAriaLabel(article, /[\d.KMkm]+\s+reposts/)),
      views: parseCount(pickAriaLabel(article, /[\d.KMkm]+\s+views/)),
      posted_at: timeM ? timeM[1] : null,
      caption: captionM ? captionM[1].trim() : "",
      thumbnail_url: null,
      hashtags: (captionM ? captionM[1] : "").match(/#\w+/g) || []
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  const score = (p) => (p.likes || 0) + 3 * (p.comments || 0) + 5 * (p.shares || 0) + 0.05 * (p.views || 0);
  return [...posts].sort((a, b) => score(b) - score(a));
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    appendScrapeLog(runId, "x", { event: "navigate", url: accountUrl });
    await page.goto(accountUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(800, 1500);

    if (/\/(login|i\/flow\/login)/i.test(page.url())) throw new Error("login_wall");

    const batches = Math.ceil(recent / 10);
    for (let i = 0; i < batches; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 3));
      await jitter(400, 1100);
      appendScrapeLog(runId, "x", { event: "scroll-batch", batch: i });
    }

    const html = await page.content();
    const posts = parseTimeline(html, accountUrl);
    appendScrapeLog(runId, "x", { event: "parsed", count: posts.length });

    return {
      platform: "x",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: rankByEngagement(posts).slice(0, top)
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-x-parse.test.mjs
```

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/x.mjs tests/scraper-x-parse.test.mjs tests/fixtures/x-profile.html
git commit -m "feat(scrape): x scraper with parse test"
```

---

## Task 11: Implement Threads scraper module

**Files:**
- Create: `scripts/scrapers/threads.mjs`
- Create: `tests/fixtures/threads-profile.html`
- Create: `tests/scraper-threads-parse.test.mjs`

- [ ] **Step 1: Create the fixture**

Threads markup mirrors IG (same Meta engineering org). Posts are wrapped in `<div data-pressable-container>` with engagement counts in nearby `<span>`:

```html
<!doctype html>
<html><body>
<main>
  <div data-pressable-container>
    <a href="/@black_magic_noirsboxes/post/AAA111"><time datetime="2026-04-22T12:00:00Z"></time></a>
    <span>Lab readout: PD 65W tested</span>
    <div aria-label="234 likes">234</div>
    <div aria-label="12 replies">12</div>
    <div aria-label="5 reposts">5</div>
  </div>
  <div data-pressable-container>
    <a href="/@black_magic_noirsboxes/post/BBB222"><time datetime="2026-04-20T08:00:00Z"></time></a>
    <span>Cable autopsy day</span>
    <div aria-label="89 likes">89</div>
    <div aria-label="2 replies">2</div>
    <div aria-label="1 repost">1</div>
  </div>
</main>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-threads-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseFeed } from "../scripts/scrapers/threads.mjs";

test("parseFeed extracts post_url, likes, replies, reposts, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/threads-profile.html", "utf8");
  const posts = parseFeed(html, "https://www.threads.net/@black_magic_noirsboxes");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.threads.net/@black_magic_noirsboxes/post/AAA111");
  assert.equal(posts[0].likes, 234);
  assert.equal(posts[0].comments, 12);
  assert.equal(posts[0].shares, 5);
  assert.equal(posts[0].caption, "Lab readout: PD 65W tested");
});
```

- [ ] **Step 3: Run, verify FAIL**

- [ ] **Step 4: Implement Threads module**

Create `scripts/scrapers/threads.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

function parseCount(text) {
  if (!text) return null;
  const m = /([\d.,]+)\s*([KkMm]?)/.exec(text);
  if (!m) return null;
  let n = Number(m[1].replace(/,/g, ""));
  if (m[2] === "K" || m[2] === "k") n *= 1000;
  if (m[2] === "M" || m[2] === "m") n *= 1_000_000;
  return Math.round(n);
}

function pickAriaLabel(block, keyword) {
  const re = new RegExp(`aria-label="([^"]*\\b${keyword}s?\\b[^"]*)"`, "i");
  const m = re.exec(block);
  return m ? m[1] : null;
}

export function parseFeed(html, baseUrl) {
  const items = html.split(/<div\s+data-pressable-container>/i).slice(1);
  const out = [];
  for (const block of items) {
    const item = '<div data-pressable-container>' + block.split(/<\/div>\s*<div\s+data-pressable-container>/i)[0];
    const hrefM = /<a\s+href="([^"]+\/post\/[^"]+)"/i.exec(item);
    if (!hrefM) continue;
    const post_url = new URL(hrefM[1], baseUrl).toString();
    const timeM = /<time\s+datetime="([^"]+)"/i.exec(item);
    const captionM = /<span>([^<]+)<\/span>/i.exec(item);
    out.push({
      post_url,
      media_type: "post",
      likes: parseCount(pickAriaLabel(item, "like")),
      comments: parseCount(pickAriaLabel(item, "repl")),
      shares: parseCount(pickAriaLabel(item, "repost")),
      views: null,
      posted_at: timeM ? timeM[1] : null,
      caption: captionM ? captionM[1].trim() : "",
      thumbnail_url: null,
      hashtags: (captionM ? captionM[1] : "").match(/#\w+/g) || []
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  const score = (p) => (p.likes || 0) + 3 * (p.comments || 0) + 5 * (p.shares || 0);
  return [...posts].sort((a, b) => score(b) - score(a));
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    appendScrapeLog(runId, "threads", { event: "navigate", url: accountUrl });
    await page.goto(accountUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(800, 1500);

    if (page.url().includes("/login")) throw new Error("login_wall");

    const batches = Math.ceil(recent / 10);
    for (let i = 0; i < batches; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 2));
      await jitter(400, 1100);
      appendScrapeLog(runId, "threads", { event: "scroll-batch", batch: i });
    }

    const html = await page.content();
    const posts = parseFeed(html, accountUrl);
    appendScrapeLog(runId, "threads", { event: "parsed", count: posts.length });

    return {
      platform: "threads",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: rankByEngagement(posts).slice(0, top)
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-threads-parse.test.mjs
```

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/threads.mjs tests/scraper-threads-parse.test.mjs tests/fixtures/threads-profile.html
git commit -m "feat(scrape): threads scraper with parse test"
```

---

## Task 12: Implement TikTok scraper module

**Files:**
- Create: `scripts/scrapers/tiktok.mjs`
- Create: `tests/fixtures/tiktok-profile.html`
- Create: `tests/scraper-tiktok-parse.test.mjs`

- [ ] **Step 1: Create the fixture**

TikTok profile uses `<div data-e2e="user-post-item">` per video, with view count in `[data-e2e=video-views]`:

```html
<!doctype html>
<html><body>
<main>
  <div data-e2e="user-post-item">
    <a href="/@noirs.boxes/video/7111111111111111111"><img src="thumb1.jpg"/></a>
    <strong data-e2e="video-views">12.3K</strong>
  </div>
  <div data-e2e="user-post-item">
    <a href="/@noirs.boxes/video/7222222222222222222"><img src="thumb2.jpg"/></a>
    <strong data-e2e="video-views">456</strong>
  </div>
</main>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-tiktok-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseProfile } from "../scripts/scrapers/tiktok.mjs";

test("parseProfile extracts post_url, views, thumbnail", () => {
  const html = readFileSync("tests/fixtures/tiktok-profile.html", "utf8");
  const posts = parseProfile(html, "https://www.tiktok.com/@noirs.boxes");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.tiktok.com/@noirs.boxes/video/7111111111111111111");
  assert.equal(posts[0].views, 12300);
  assert.equal(posts[0].thumbnail_url, "thumb1.jpg");
  assert.equal(posts[1].views, 456);
});
```

- [ ] **Step 3: Run, verify FAIL**

- [ ] **Step 4: Implement TikTok module**

Create `scripts/scrapers/tiktok.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

function parseCount(text) {
  if (!text) return null;
  const m = /([\d.,]+)\s*([KkMm]?)/.exec(text);
  if (!m) return null;
  let n = Number(m[1].replace(/,/g, ""));
  if (m[2] === "K" || m[2] === "k") n *= 1000;
  if (m[2] === "M" || m[2] === "m") n *= 1_000_000;
  return Math.round(n);
}

export function parseProfile(html, baseUrl) {
  const items = html.split(/<div\s+data-e2e="user-post-item">/i).slice(1);
  const out = [];
  for (const block of items) {
    const item = '<div data-e2e="user-post-item">' + block.split(/<\/div>/i)[0];
    const hrefM = /<a\s+href="([^"]+)"/i.exec(item);
    if (!hrefM) continue;
    const post_url = hrefM[1].startsWith("http") ? hrefM[1] : new URL(hrefM[1], baseUrl).toString();
    const viewsM = /data-e2e="video-views"[^>]*>([^<]+)/i.exec(item);
    const thumbM = /<img[^>]*src="([^"]+)"/i.exec(item);
    out.push({
      post_url,
      media_type: "video",
      likes: null,
      comments: null,
      shares: null,
      views: viewsM ? parseCount(viewsM[1]) : null,
      posted_at: null,
      caption: "",
      thumbnail_url: thumbM ? thumbM[1] : null,
      hashtags: []
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  return [...posts].sort((a, b) => (b.views || 0) - (a.views || 0));
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    appendScrapeLog(runId, "tiktok", { event: "navigate", url: accountUrl });
    await page.goto(accountUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(1000, 2000);

    if (page.url().includes("/login")) throw new Error("login_wall");

    const batches = Math.ceil(recent / 12);
    for (let i = 0; i < batches; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 3));
      await jitter(600, 1500);
      appendScrapeLog(runId, "tiktok", { event: "scroll-batch", batch: i });
    }

    const html = await page.content();
    const posts = parseProfile(html, accountUrl);
    appendScrapeLog(runId, "tiktok", { event: "parsed", count: posts.length });

    return {
      platform: "tiktok",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: rankByEngagement(posts).slice(0, top)
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-tiktok-parse.test.mjs
```

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/tiktok.mjs tests/scraper-tiktok-parse.test.mjs tests/fixtures/tiktok-profile.html
git commit -m "feat(scrape): tiktok scraper with parse test"
```

---

## Task 13: Implement YouTube scraper module

**Files:**
- Create: `scripts/scrapers/youtube.mjs`
- Create: `tests/fixtures/youtube-channel.html`
- Create: `tests/scraper-youtube-parse.test.mjs`

- [ ] **Step 1: Create the fixture**

YouTube channel "/videos" tab uses `<ytd-rich-item-renderer>` with `<a id="thumbnail">` and `<span id="metadata-line">` for views/age:

```html
<!doctype html>
<html><body>
<ytd-rich-item-renderer>
  <a id="thumbnail" href="/watch?v=AAA111"><img src="thumb1.jpg"/></a>
  <a href="/watch?v=AAA111" id="video-title-link" title="PD 65W lab test">PD 65W lab test</a>
  <div id="metadata-line"><span>12K views</span><span>2 weeks ago</span></div>
</ytd-rich-item-renderer>
<ytd-rich-item-renderer>
  <a id="thumbnail" href="/watch?v=BBB222"><img src="thumb2.jpg"/></a>
  <a href="/watch?v=BBB222" id="video-title-link" title="MFi check">MFi check</a>
  <div id="metadata-line"><span>456 views</span><span>1 month ago</span></div>
</ytd-rich-item-renderer>
</body></html>
```

- [ ] **Step 2: Write the failing parse test**

Create `tests/scraper-youtube-parse.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseChannelVideos } from "../scripts/scrapers/youtube.mjs";

test("parseChannelVideos extracts post_url, title, views, thumbnail", () => {
  const html = readFileSync("tests/fixtures/youtube-channel.html", "utf8");
  const posts = parseChannelVideos(html, "https://www.youtube.com/@boxesnoirs");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.youtube.com/watch?v=AAA111");
  assert.equal(posts[0].caption, "PD 65W lab test");
  assert.equal(posts[0].views, 12000);
  assert.equal(posts[0].thumbnail_url, "thumb1.jpg");
  assert.equal(posts[1].views, 456);
});
```

- [ ] **Step 3: Run, verify FAIL**

- [ ] **Step 4: Implement YouTube module**

Create `scripts/scrapers/youtube.mjs`:

```js
import { withBrowser, jitter, appendScrapeLog } from "./_shared.mjs";

function parseCount(text) {
  if (!text) return null;
  const m = /([\d.,]+)\s*([KkMm]?)\s*views?/i.exec(text);
  if (!m) return null;
  let n = Number(m[1].replace(/,/g, ""));
  if (m[2] === "K" || m[2] === "k") n *= 1000;
  if (m[2] === "M" || m[2] === "m") n *= 1_000_000;
  return Math.round(n);
}

export function parseChannelVideos(html, baseUrl) {
  const items = html.split(/<ytd-rich-item-renderer[\s>]/i).slice(1);
  const out = [];
  for (const block of items) {
    const item = '<ytd-rich-item-renderer>' + block.split(/<\/ytd-rich-item-renderer>/i)[0];
    const hrefM = /<a[^>]*id="thumbnail"\s+href="([^"]+)"/i.exec(item);
    if (!hrefM) continue;
    const post_url = new URL(hrefM[1], baseUrl).toString();
    const titleM = /id="video-title-link"\s+title="([^"]+)"/i.exec(item);
    const metaM = /id="metadata-line"[^>]*>([\s\S]*?)<\/div>/i.exec(item);
    const thumbM = /<img[^>]*src="([^"]+)"/i.exec(item);
    out.push({
      post_url,
      media_type: "video",
      likes: null,
      comments: null,
      shares: null,
      views: metaM ? parseCount(metaM[1]) : null,
      posted_at: null,
      caption: titleM ? titleM[1] : "",
      thumbnail_url: thumbM ? thumbM[1] : null,
      hashtags: []
    });
  }
  return out;
}

export function rankByEngagement(posts) {
  return [...posts].sort((a, b) => (b.views || 0) - (a.views || 0));
}

export async function scrape({ accountUrl, recent, top, profileDir, runId }) {
  return await withBrowser(profileDir, async (ctx) => {
    const page = await ctx.newPage();
    const url = accountUrl.endsWith("/videos") ? accountUrl : accountUrl.replace(/\/$/, "") + "/videos";
    appendScrapeLog(runId, "youtube", { event: "navigate", url });
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await jitter(1000, 2000);

    if (page.url().includes("/accounts/SetSID")) throw new Error("login_wall");

    const batches = Math.ceil(recent / 12);
    for (let i = 0; i < batches; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight * 3));
      await jitter(600, 1500);
      appendScrapeLog(runId, "youtube", { event: "scroll-batch", batch: i });
    }

    const html = await page.content();
    const posts = parseChannelVideos(html, accountUrl);
    appendScrapeLog(runId, "youtube", { event: "parsed", count: posts.length });

    return {
      platform: "youtube",
      account_url: accountUrl,
      scraped_at: new Date().toISOString(),
      recent_count: posts.length,
      top: rankByEngagement(posts).slice(0, top)
    };
  });
}
```

- [ ] **Step 5: Run, verify PASS**

```bash
node --test tests/scraper-youtube-parse.test.mjs
```

- [ ] **Step 6: Commit**

```bash
git add scripts/scrapers/youtube.mjs tests/scraper-youtube-parse.test.mjs tests/fixtures/youtube-channel.html
git commit -m "feat(scrape): youtube scraper with parse test"
```

---

## Task 14: End-to-end smoke test — `/weekly-plan` single platform

**Files:** none modified (live verification)

- [ ] **Step 1: Run the full test suite**

```bash
npm test
```

Expected: all tests pass — `plan-export`, `scrape-cli`, `scraper-{instagram,facebook,x,threads,tiktok,youtube}-parse`. Total ~10 tests.

- [ ] **Step 2: Manually invoke the orchestrator path for one platform**

There is no automated runner for `/weekly-plan` — it's a Claude slash command. So the smoke is:

1. Open Claude Code in the repo.
2. Run: `/weekly-plan --week 2026-W19`
3. Watch the orchestrator follow the new step list.

For a faster smoke that doesn't burn the full pipeline, you can instead call the script directly:

```bash
RUN_ID=smoke-$(date +%s)
node scripts/scrape-top-posts.mjs --brand noirs-boxes --platform instagram \
  --account-url https://www.instagram.com/black_magic_noirsboxes/ \
  --recent 30 --top 5 \
  --out reports/plans/noirs-boxes/2026-W19/research/own-instagram-top.json \
  --run-id "$RUN_ID"
```

- [ ] **Step 3: Synthesize a minimal plan.json and export**

Without running the full Claude orchestration, build a tiny plan.json by hand to verify the export end-to-end:

```bash
mkdir -p reports/plans/noirs-boxes/2026-W19
cat > reports/plans/noirs-boxes/2026-W19/plan.json <<'JSON'
{
  "schedule": [{"slot_id":"2026-W19-ig-mon-1230","weekday":"Mon","time_local":"12:30","platform":"instagram","mode":"post","theme":"MFi check demo","product_id":"md-905","caption":"...","hashtags":["#mfi","#charging"],"media_path":"","reference_urls":[],"status":"planned","posted_url":"","posted_at":"","draft_id":"weekly-2026-W19-ig-mon-1230"}],
  "frequency": [{"platform":"instagram","posts_per_week":4,"preferred_weekdays":["Mon","Wed","Fri","Sun"],"preferred_times":["12:30","20:00"],"rationale":"smoke"}],
  "topic_research": [{"platform":"instagram","competitor_product":"ChargerLAB POWER-Z","similar_to":"md-903","relevant_to":"md-903","post_url":"https://www.instagram.com/p/X/","posted_at":"2026-04-01","likes":100,"comments":5,"shares":0,"views":1000,"hook":"PD test","tone":"technical-demo","layout":"video","why_it_resonated":"shows real readings","takeaway_for_us":"lead with on-screen number"}],
  "own_history": [{"platform":"instagram","post_url":"https://www.instagram.com/p/Y/","posted_at":"2026-04-15","likes":50,"comments":3,"shares":0,"views":500,"caption_excerpt":"PD test","tone":"technical","layout":"reel","hook":"Did you know","why_it_resonated":"specific reading","repeatable_pattern":"lead with the number"}],
  "metrics": [],
  "meta": {"brand":"noirs-boxes","iso_week":"2026-W19","generated_at":"2026-05-10T00:00:00Z","prev_week_plan_path":null,"own_top_scraped_at":"2026-05-10T00:00:00Z","model":"claude-opus-4-7","notes":"smoke"}
}
JSON

node scripts/plan-export.mjs reports/plans/noirs-boxes/2026-W19/plan.json
```

Expected: stdout prints the xlsx path. File exists.

- [ ] **Step 4: Open the xlsx and verify visually**

On WSL the simplest way is to open from File Explorer (the repo is on `/mnt/c/Users/Ron/Desktop/...`). Or run:

```bash
explorer.exe reports/plans/noirs-boxes/2026-W19/
```

Expected: 6 tabs in this order — TopicResearch, OwnHistory, Frequency, Schedule, Metrics, Meta. Each non-empty sheet shows the headers and the synthesized rows. Metrics is empty (no header row drift).

- [ ] **Step 5: Acceptance gate**

Cross-check against design spec §10:

- [ ] Brand YAML free of mystery/occult framing — `grep -iE 'mystery|occult|collectible' config/brands/noirs-boxes.yaml` returns nothing.
- [ ] Both SKUs present — `grep -E 'id: md-90[35]' config/brands/noirs-boxes.yaml | wc -l` returns `2`.
- [ ] Scrape script runs and returns a JSON for at least IG (Step 2).
- [ ] xlsx has 6 sheets in expected order (Step 4).
- [ ] Schedule row has non-null `product_id` (the synthesized JSON has `md-905`; in a real `/weekly-plan` run this comes from `weekly-plan-draft`).
- [ ] `data/scrape-logs/<run-id>-instagram.jsonl` exists (Step 2).

- [ ] **Step 6: Final commit + tag**

```bash
git add -A
git commit -m "chore: smoke verification of strategy deliverable end-to-end"
git tag v0.2.0-strategy-deliverable
```

(Skip `git tag` if not using git.)

---

## Out of scope (do NOT implement here)

- Playwright scrapers for AVHzY / WITRN / FNIRSI socials (their accounts are unverified — locked at 3 entries during brainstorming).
- Switching `weekly-plan-review` from MCP to script (decision D6).
- Profile cloning / parallel-platform scraping (decision §5 of spec).
- Reviewer-creator topic research (Big Clive / Voltlog / Louis Rossmann — explicitly de-scoped).
- New `/strategy` command (folded into existing `/weekly-plan`).
- Image generation pipeline changes.
- Auto-discovering competitors or auto-refresh schedules.

If the implementer encounters an issue that requires touching one of the above, stop and surface — don't expand scope.
