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
