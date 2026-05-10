---
name: fetch-reference
description: Pull the main content (title / body / key images) of an external URL for draft-* skills. Multi-layer fallback against bot blockers.
---

> Common rules: `docs/OPERATING_RULES.md`. This skill turns a URL into usable text. It does not draft posts.

## Input
- `url`: target URL (single).
- `purpose`: caller's intent (lets the LLM know what to keep, e.g. "drafting an IG post about an unboxing — keep visual cues and product highlights").

## Output (JSON)
```json
{
  "url": "...",
  "title": "...",
  "main_text": "ad/nav/footer-stripped main text",
  "summary": "3-8 sentence summary tuned to purpose",
  "key_points": ["...", "..."],
  "images": ["https://...absolute..."],
  "fetched_via": "webfetch | curl | playwright",
  "fetched_at": "<ISO>"
}
```

Failure: `{ "error": "<reason>", "tried": ["webfetch", "curl", "playwright"] }`

## Strategy (try in order; advance only on failure)

### Layer 1 — `WebFetch`

`WebFetch(url, prompt="extract title, main text, image URLs as JSON")`.

Treat as failed if:
- Tool errors / times out.
- Body is clearly a login wall, paywall, or Cloudflare challenge ("Just a moment", "Verify you are human", login prompt).
- `main_text` < 100 chars (likely blocked).

### Layer 2 — `curl` with realistic browser headers

```bash
curl -sL --max-time 30 \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en;q=0.9,zh-TW;q=0.8" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Sec-Fetch-Dest: document" \
  -H "Sec-Fetch-Mode: navigate" \
  -H "Sec-Fetch-Site: none" \
  -H "Upgrade-Insecure-Requests: 1" \
  --compressed \
  "$URL" -o /tmp/fetch-ref-$$.html
```

Then `Read /tmp/fetch-ref-$$.html` (first 200KB), parse `<title>`, `<meta property="og:*">`, `<article>` / `<main>` / largest `<div>` text. Delete the temp file when done. Same failure signals as Layer 1.

### Layer 3 — Playwright (last resort)

Slow, must clean up the browser:

1. `mcp__playwright__browser_navigate` → `url`
2. `mcp__playwright__browser_wait_for({ time: 2 })`
3. `mcp__playwright__browser_snapshot`
4. (optional) `browser_evaluate`:
   ```js
   () => {
     const a = document.querySelector('article, main, [role=main]') || document.body;
     return {
       title: document.title,
       text: a.innerText.slice(0, 20000),
       images: [...document.querySelectorAll('img')].map(i => i.src).filter(Boolean).slice(0, 20)
     };
   }
   ```
5. **Always** `mcp__playwright__browser_close` (this skill owns cleanup).

## Summarize step

After getting `main_text`:
- 3-8 `key_points`.
- One `summary` ≤ 200 words tuned to `purpose`.
- Filter `images` to drop logos/icons (size hints in URL or filename: `logo`, `icon`, `avatar`).

## Don'ts

- Do not call other skills (no `draft-*`, no `publish-*`).
- Do not write fetched content to any repo file — return JSON only.
- Do not retry the same layer more than once.
- Do not bypass paywalls or login walls — return `{ error: "paywall or login required" }`.
- Do not skip `browser_close` in Layer 3.
- Do not omit `User-Agent` / `Accept-Language` in Layer 2.
