import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import ExcelJS from "exceljs";

test("plan-export emits 5 sheets with TopicResearch", async () => {
  const dir = mkdtempSync(join(tmpdir(), "plan-export-"));
  const planPath = join(dir, "plan.json");
  writeFileSync(
    planPath,
    JSON.stringify({
      meta: { brand: "noirs-boxes", iso_week: "2026-W19", generated_at: "2026-05-10T00:00:00Z", model: "claude-opus-4-7" },
      schedule: [{ slot_id: "2026-W19-ig-mon-1230", weekday: "Mon", time_local: "12:30", platform: "instagram", mode: "post", theme: "MFi check demo", product_id: "md-905", caption: "...", hashtags: ["#mfi"], media_path: "x.jpg", reference_urls: [], status: "planned", posted_url: "", posted_at: "", draft_id: "weekly-2026-W19-ig-mon-1230" }],
      frequency: [{ platform: "instagram", posts_per_week: 4, preferred_weekdays: ["Mon"], preferred_times: ["12:30"], rationale: "test" }],
      topic_research: [{ platform: "instagram", competitor_product: "ChargerLAB POWER-Z", similar_to: "md-903", relevant_to: "md-903", post_url: "https://...", posted_at: "2026-04-01", likes: 100, comments: 5, shares: 0, views: 1000, hook: "test hook", tone: "technical-demo", layout: "video + caption", why_it_resonated: "shows real protocol", takeaway_for_us: "use TFT readouts" }],
      metrics: []
    })
  );

  execFileSync("node", ["scripts/plan-export.mjs", planPath], { stdio: "inherit" });

  const xlsxPath = join(dir, "2026-W19-0504-0510.xlsx");
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(xlsxPath);
  const names = wb.worksheets.map((w) => w.name);
  assert.deepEqual(names, ["TopicResearch", "Frequency", "Schedule", "Metrics", "Meta"]);

  const tr = wb.getWorksheet("TopicResearch");
  const trHeader = tr.getRow(1).values.slice(1);
  assert.deepEqual(trHeader, ["platform", "competitor_product", "similar_to", "relevant_to", "post_url", "posted_at", "likes", "comments", "shares", "views", "hook", "tone", "layout", "why_it_resonated", "takeaway_for_us"]);
  assert.equal(tr.getCell("B2").value, "ChargerLAB POWER-Z");
});
