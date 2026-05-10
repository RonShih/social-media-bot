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
