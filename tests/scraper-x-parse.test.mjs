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
