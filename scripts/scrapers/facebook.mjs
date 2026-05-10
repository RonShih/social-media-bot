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
