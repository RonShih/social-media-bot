---
description: Phase 1 — draft posts per platform for user review. Preview only, never publishes. One subagent per platform, parallel.
argument-hint: "[platforms (csv: fb,ig,x,threads,yt,tt)] [--url <ref>] [other hints]"
---

Phase 1 of the two-stage publish flow. Spawn one draft subagent per platform; reply to the user with the preview; write `reports/drafts/<brand>/<draft_id>.json`. The user confirms via `ok` / `go` / `yes` / `/publish-now draft:<id>` to trigger Phase 2.

## Steps

1. Parse intent from:
   - Command args (`fb,ig,x,threads,yt,tt`).
   - Channel message body + uploaded media (TG inbox path: `~/.claude/channels/telegram/inbox/<id>.{jpg,png,mp4,mov}`).
   - Any URLs in the message — every `https?://...` is a "reference" that needs fetching.
   - Active brand YAML — pick the most appropriate `product_id` and `theme` from `products[]` and `content_themes[]` based on the user's intent.
   - Conversation context.

2. Resolve the active brand: read `BRAND` env, then `config/active-brand`.

3. Generate `draft_id` = `YYYYMMDD-HHMMSS` (use `date +%Y%m%d-%H%M%S`). All platforms in this batch share one id.

4. If reference URLs exist, spawn `fetch-reference` subagent(s) **before** the draft subagents:
   - `subagent_type: general-purpose`
   - Prompt: "Read `.claude/skills/fetch-reference/SKILL.md`, then run the three-layer fallback for `<url>`. `purpose`: `<derive from message intent>`. Return JSON exactly per SKILL.md output schema."
   - Multiple URLs → multiple parallel Agent calls in one message.
   - On failure → reply to user: "Could not fetch <url>. Reply with text or a different URL, or say 'continue without' to draft anyway." Stop until user decides; do not silently proceed with empty references.

5. Spawn one subagent per platform in **parallel** (one message, multiple Agent calls):

   | platform | skill | required input |
   |---|---|---|
   | `facebook` | `draft-facebook` | product_id, theme, language, mode, local_image_path / local_video_path |
   | `instagram` | `draft-instagram` | same |
   | `x` | `draft-x` | same (image / video optional) |
   | `threads` | `draft-threads` | same (image / video optional) |
   | `youtube` | `draft-youtube` | product_id, theme, language, local_video_path, format |
   | `tiktok` | `draft-tiktok` | product_id, theme, language, local_video_path |

   Each subagent prompt must include:
   - "Read `.claude/skills/draft-<platform>/SKILL.md`, follow its input/output schema, return JSON only."
   - The active brand YAML path.
   - Inputs for that platform.
   - If reference data exists → embed as `extra.reference = {...}` (the whole `fetch-reference` JSON).
   - "Do not call publish-* / fetch-reference / open browser / write files. Return JSON only."

6. Aggregate (main session, not a subagent):

   ```json
   {
     "draft_id": "<id>",
     "brand": "<slug>",
     "created_at": "<ISO>",
     "references": [<fetch-reference JSON>, ...],
     "drafts": [<draft JSON>, ...],
     "errors": [{"platform": "...", "error": "..."}]
   }
   ```

   Write to `reports/drafts/<brand>/<draft_id>.json`.

7. Write a pending-confirmation entry to `data/pending-confirmations.json`:

   ```json
   {
     "<draft_id>": {
       "preview_sent_at": "<ISO>",
       "platforms": ["facebook","instagram"],
       "expires_at": "<now + 5min>",
       "channel": "telegram | line | cli"
     }
   }
   ```

8. Reply (TG `reply` for channel sessions; main session text for terminal). **Plain text, no markdown.** One reply per draft batch:

   ```
   📝 Draft <draft_id>
   refs: <url1> (via <fetched_via>)
         <url2> (via <fetched_via>)

   facebook
   <caption + hashtags preview>

   instagram
   <...>

   ----
   ✅ confirm all: reply ok / go / yes (or /publish-now draft:<id>)
   ✏️ edit one: reply "edit fb: <new content>"
   ❌ cancel: reply "cancel <draft_id>"
   ```

## Failure handling

- Any platform subagent returns `error` → record in `errors`, others continue, surface in the reply.
- All platforms fail → still write the draft JSON (errors-only) for debugging.

## Verification

- [ ] `reports/drafts/<brand>/<draft_id>.json` written.
- [ ] `data/pending-confirmations.json` updated.
- [ ] Single reply with all platform previews.
- [ ] No browser opened (drafting is pure LLM).

## Don'ts

- Do not call `publish-*` skills.
- Do not `WebFetch` / `curl` / open Playwright in the main session for reference URLs — always spawn a `fetch-reference` subagent.
- Do not write multiple files for one draft batch — one JSON per draft id.
- Do not draft in the main session — always spawn subagents, even for a single platform.
- If reference fetching fails, do not fabricate "url + title" content — stop and ask the user.
