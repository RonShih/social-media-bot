import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseFeed } from "../scripts/scrapers/threads.mjs";

test("parseFeed extracts post_url, likes, replies, reposts, posted_at, caption", () => {
  const html = readFileSync("tests/fixtures/threads-profile.html", "utf8");
  const posts = parseFeed(html, "https://www.threads.net/@black_magic_noirsboxes");
  assert.equal(posts.length, 2);

  assert.equal(posts[0].post_url, "https://www.threads.net/@black_magic_noirsboxes/post/AAA111");
  assert.equal(posts[0].likes, 234);
  assert.equal(posts[0].comments, 12);
  assert.equal(posts[0].shares, 5);
  assert.equal(posts[0].caption, "Lab readout: PD 65W tested");
});
