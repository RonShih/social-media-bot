# LINE channel discipline

When you (Claude) are a `claude -p` session spawned via `bridge/line/webhook_server.py`, these rules **override** the TG-specific parts of `docs/OPERATING_RULES.md`. Everything else (error handling, browser lifecycle, click-log, step_id locking, etc.) remains unchanged.

How to detect: your prompt starts with "You are handling a message for a LINE ..." or the environment variable `LINE_TARGET_ID` is set.

---

## 1. All LINE replies go through `mcp__line__line_send`

OPERATING_RULES §1 says "TG messages go through `mcp__plugin_telegram_telegram__reply`" — not applicable for LINE.

LINE uses tools exposed by the LINE MCP server:

| Tool | Purpose |
|---|---|
| `line_send` | **Use this by default.** Automatically decides between reply (first call, within 30s) and push (afterwards / token already used) |
| `line_reply` | Force use of reply_token (for manual control) |
| `line_push` | Force use of push API (for long-running tasks where reply is known to be expired) |

**The main session's stdout is NOT pushed back to LINE — nothing sent via line_send = user sees nothing.**

## 2. One user message → only one reply

OPERATING_RULES §2 says "react with an emoji to acknowledge, reply with progress for long tasks, edit_message to update" — **none of this applies in LINE**:
- LINE does not support reactions (no lightweight "acknowledged" signal)
- LINE does not support edit_message (cannot silently update progress)
- LINE push messages have a monthly quota (200 messages on free plan)

**The discipline is: send exactly 1 message per user message — and always use reply (free, unlimited).**

Specifically:

- Whether the task takes 1 second or 3 minutes, **wait until the task is fully complete, then call `line_send` once** with the final result
- Don't send "processing..." as a progress signal — save the reply token for the final result
- Failures also get a single reply that wraps up the error — don't "first say trying" then "then say failed"

> Why not send "processing"? Because sending it uses up the only reply token, and the actual result would have to go through push (consuming quota). It's better for the user to wait 30 seconds with no visible activity and then receive the complete answer in one go.
>
> Exception: if the task might genuinely take longer than 30 seconds (reply token will expire) → call `line_send` with the current progress before the 25-second mark (uses the reply token), then finish via push. The `line_send` tool handles the reply→push switch automatically.

## 3. Message format: plain text, brief, no markdown — same as TG

All rules from OPERATING_RULES §3 apply to LINE **in full**:

- LINE does not render markdown by default — tables / `#` headings / `**bold**` / `*italic*` / `code` / nested bullets all become garbled text
- Paste URLs directly, don't use `[text](url)`
- Lead with the conclusion, ≤ 5 sentences, leading emoji indicates type (✅ ❌ ⚠️ 📌)
- One emoji is enough — don't stack them

The only difference: LINE Messaging API has no toggle for markdown rendering (Telegram has `format: "markdownv2"`), so this discipline is hard and non-negotiable.

## 4. reply_token 30-second limit

LINE's `reply_token` must be used within **30 seconds** of when the webhook arrived, and can only be used once. `line_send` handles this automatically:

- First call to `line_send` → uses reply_token
- Subsequent calls (or if token was already used) → falls back to push

You don't need to worry about the logic. But **the first `line_send` must go out within 30 seconds**. If you estimate a multi-platform publish will take 2 minutes, **your first action** should be to `line_send` one line to claim the reply token — don't wait for results before saying anything.

## 5. push is a fallback, not normal — quota should almost never be used

Our design goal: **always 0 push, everything via reply**.

How `line_send` works:
- First call (reply token not yet used) → uses reply (free)
- Subsequent calls → falls back to push (consumes quota)

As long as you send exactly 1 `line_send` per user message and do so within 30 seconds, push will never be touched.

When will push actually be triggered?
1. Task runs longer than 30 seconds (reply token expired) → push is unavoidable at that point
2. You violate §2 discipline by sending a second message

Both should be avoided. When `line_send` returns `{"ok": true, "method": "push"}` that's a signal — this task violated the reply-only design; correct it in your next reasoning pass.

If push quota runs out, `line_send` returns `{"ok": false, "info": "...quota..."}` — **do not retry**. Log to stdout only (L1 will capture it, visible next time bot is mentioned).

## 6. Group vs 1:1 — already filtered by webhook

Messages that reach you (Claude) always satisfy one of:
- 1:1 chat
- Group / multi-person chat with bot mention or matching prefix (`@editor`, `/sma`, etc.)

The prompt header tells you `target_id` (group_id / user_id) and `sender` (in groups this is the speaking member's user_id, not the whole group). When replying:

- Whether 1:1 or group, always use **`line_send`** (push goes to the whole group / 1:1 chat)
- Don't @ reply a specific member in a group (unless you can get their displayName and naming them is genuinely needed) — LINE @mention experience is not as clean as Slack

## 7. Media

- Images / videos / audio uploaded by the user → already downloaded to `media/inbox/line/<group_id>/<message_id>.<ext>` by webhook
- The "[Current message attachment]" section of the prompt gives the absolute path
- Don't delete, don't re-fetch from URL
- **Sending images back is not supported yet** (Phase 1 has no ephemeral file host) — for visual information, describe it in text

## 8. Memory layers

- **L1 conversation buffer** (most recent 20 messages) is already injected at the start of your prompt — no need to read `data/line/conversations/`
- **L2 structured preferences** (`data/line/memory/<group_id>.md`) is also injected — but **things worth remembering long-term** (brand preferences, rules, client habits, feedback on last post) should be actively written to this file via the Edit tool. Automatically included next spawn.
- Criteria for writing to L2:
  - ✅ Write: "This group / client doesn't want emoji" "Brand color: green #1A7F3D" "Thursday is the fixed IG posting day" "Client said last caption was too long"
  - ❌ Don't write: details specific to this task (ephemeral), facts visible in code, history visible in git
- L3 content history (SQLite index of past posts) is **not yet implemented** (Phase 2) — to look up past posts use `Glob`/`Read` on `reports/posts/*.md`.

## 9. Error handling — consistent with OPERATING_RULES §4

Swallow intermediate noise silently, report final outcome honestly. The only difference is "replying to user" means one `line_send` message instead of TG's `reply`.

Hard rules remain: don't fabricate post_url, don't click buttons with unclear purpose, don't grab profile lock, don't auto-fill passwords.

## 10. Main session stdout is a dev log, not a response

This is the biggest conceptual difference between LINE and TG:

- TG channel: main session text output **equals** the reply to the user (plugin intercepts it)
- LINE bridge: main session stdout is only a dev log visible in the terminal. **Only `line_send` is ever seen by the user.**

So even if you write the complete answer to stdout, the user won't see it. You must call `line_send`.
