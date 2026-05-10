import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parsePage } from "../scripts/scrapers/facebook.mjs";

test("parsePage extracts post_url, type, likes, comments, shares, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/facebook-page.html", "utf8");
  const posts = parsePage(html, "https://www.facebook.com/BlackMagicNoirsBoxes/");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.facebook.com/BlackMagicNoirsBoxes/posts/1111111111111");
  assert.equal(posts[0].media_type, "post");
  assert.equal(posts[0].likes, 234);
  assert.equal(posts[0].comments, 12);
  assert.equal(posts[0].shares, 5);
  assert.equal(posts[0].caption, "Lab readout: PD 65W tested");

  assert.equal(posts[1].media_type, "video");
  assert.equal(posts[1].likes, 1200); // "1.2K"
});
