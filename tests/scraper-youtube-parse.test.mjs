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
