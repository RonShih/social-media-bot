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
