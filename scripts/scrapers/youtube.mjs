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
