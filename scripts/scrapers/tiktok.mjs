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
