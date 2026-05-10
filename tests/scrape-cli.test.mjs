import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

test("scrape-top-posts errors on missing --platform", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err, "expected non-zero exit");
  const stderr = err.stderr.toString();
  assert.match(stderr, /--platform required/);
});

test("scrape-top-posts errors on unknown platform", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs", "--platform", "myspace", "--account-url", "https://x", "--out", "/tmp/x.json"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err);
  assert.match(err.stderr.toString(), /unknown platform: myspace/);
});

test("scrape-top-posts errors on missing --account-url", () => {
  let err;
  try {
    execFileSync("node", ["scripts/scrape-top-posts.mjs", "--platform", "instagram", "--out", "/tmp/x.json"], { stdio: "pipe" });
  } catch (e) { err = e; }
  assert.ok(err);
  assert.match(err.stderr.toString(), /--account-url required/);
});
