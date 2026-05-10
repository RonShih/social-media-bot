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
  const re = new RegExp(`aria-label="([^"]*\\b${keyword}\\w*\\b[^"]*)"`, "i");
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
