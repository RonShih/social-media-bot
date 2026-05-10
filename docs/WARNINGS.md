# Warnings

Things that have bitten people before. Read once; refer back when the matching error appears.

## Browser lifecycle

- `mcp__playwright__browser_close` is mandatory at the end of every Playwright run. Skipping it leaves the Chromium profile locked and the next run fails immediately.
- Chromium allows one process per profile directory at a time. Per-brand profiles (`browser_profiles/<brand>/`) keep brands isolated, but two simultaneous flows for the *same* brand still collide. Serialize them.

## "WhatsApp button" trap (Facebook)

After publishing on a Facebook page, a dialog can appear titled "讓用戶輕鬆與你聯絡" / "Make it easy for users to contact you." It offers an "Add WhatsApp button" CTA. Clicking that button silently aborts the publish — the post never goes out and FB does not warn. Always click "Not now" / "稍後再說" or press Escape. `publish-facebook/SKILL.md` covers this.

## Identity-mismatch silent failure (Facebook)

If you forget the "Switch to page" / "立即切換" banner step, FB happily publishes to your personal timeline without warning. `publish-facebook` checks the page identity badge before clicking Post.

## Instagram .mov uploads

Instagram occasionally hangs on `.mov` Reel uploads at the encoder step. The fix in `publish-instagram` is to copy / rename to `.mp4` (no transcoding — IG accepts the H.264 inside). Source files stay untouched.

## Threads identity

Threads logs in via Instagram. First-time-login goes to `https://www.threads.net/login` after IG so the Threads-specific permission grant happens. Logged-in IG cookies alone are insufficient.

## YouTube delete is "move to trash"

YT does not hard-delete from Studio. Videos sit in trash for 30 days before final removal. The round-trip "verified gone" check accepts a "Video unavailable" page, not a 404. If you need true immediate removal for compliance, do it from `https://www.youtube.com/your-trash/` manually.

## TikTok re-auth on delete

TikTok throws CAPTCHA / SMS challenges on destructive actions every ~30 days. `delete-tiktok` does not solve the challenge — it returns `tiktok_reauth_required` and the orchestrator surfaces to user. Solve the challenge in a manual Chromium tab, then retry.

## X 280-char hard cap

`draft-x` enforces ≤ 280 chars total (caption + hashtags + spaces). `publish-x` will refuse silently-truncated content; if drafting cannot fit, draft returns `error: "cannot fit caption + hashtags in 280 chars"`. Fix the caption, do not bypass.

## Process noise vs end-state truth

OPERATING_RULES §5 is the most important discipline. Mid-flow dialogs, slow loads, transient errors → solve silently, do not surface. Anything that changes the user's world (publish ran but URL missing, login expired, asset missing) → return structured JSON with the exact error code, never invent a result.

Concrete rule: never fabricate a `post_url`. If extraction fails after both Business Suite and profile-grid fallbacks → return `{ "post_url": null, "error": "url_extraction_failed", "note": "post may have published, please verify manually" }`.

## Plan files

- `plan.json` is canonical. `plan.xlsx` is a view, regenerated whenever the JSON changes.
- Editing `plan.xlsx` directly does not flow back to JSON unless you run `node scripts/plan-import.mjs <plan.xlsx>` first (which writes `plan.imported.json`).
- `/publish-from-plan` reads `plan.json`, never the xlsx.

## Action log retention

Append-only. Not auto-rotated. After a few months of heavy use, `data/action-logs/` and `data/runs/` will grow. Plan a manual quarterly archive (tarball + clear the live folders).

## Image generator

Defaults to OpenAI Images (provide `OPENAI_API_KEY` via env). Falls back to library-pick when the key is absent. Image generation is NOT free — every `image_generator` call with `source: generated` costs API credits.

## Don'ts cheat-sheet

- Do not auto-fill credentials.
- Do not `pkill chrome` / `kill -9` / delete `SingletonLock`.
- Do not modify `media/`, `browser_profiles/`, or `.claude/` from `/setup`.
- Do not call skills from inside skills.
- Do not write run-level logs to `logs/` (action log is the only run-level log).
- Do not push competitor scraping into the logged-in browser.
- Do not parallelize publish flows for the same brand.
- Do not commit `config/secrets.yaml` or `browser_profiles/`.
