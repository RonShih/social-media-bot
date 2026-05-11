"""LINE webhook server.

Receives LINE webhooks → verify signature → download media → inject memory → spawn `claude -p` headless.
Claude replies to LINE via tools exposed by line_mcp_server.

Stream-json mode: `claude -p` runs with `--output-format stream-json --verbose` so every tool call
and sub-message is streamed back as one JSON object per line. Each run gets a folder under
`data/line/runs/<run_id>/` with `prompt.txt`, `events.jsonl`, `summary.log`, `stderr.log`, `meta.json` —
the user can `tail -f summary.log` to see exactly what the headless agent is doing.

Per-target concurrency lock: only one `claude -p` runs at a time per LINE group/user. Subsequent
messages while the lock is held get an immediate "previous task still running" reply (uses that
event's reply_token, free). This prevents quota burns when the user impatiently re-sends prompts.

Slow-command pre-ack: messages mentioning /weekly-plan, /publish-from-plan, "weekly plan", "週計劃"
get an immediate ack via reply_token, and the LINE MCP server is pre-marked as reply-token-used —
the final result is delivered via push. The agent timeout is bumped to CLAUDE_TIMEOUT_SLOW_SECONDS.

Start:
    cd <repo>
    bridge/line/.venv/bin/python bridge/line/webhook_server.py
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

# ensure sibling modules are importable (when running directly as: python bridge/line/webhook_server.py)
sys.path.insert(0, str(Path(__file__).parent))

import memory  # noqa: E402
from group_filter import parse_prefixes, should_respond  # noqa: E402

# ---------- env ----------

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(Path(__file__).parent / ".env")

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "127.0.0.1")
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8000"))
GROUP_PREFIXES = parse_prefixes(os.environ.get("LINE_GROUP_PREFIXES"))
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT_SECONDS", "600"))
CLAUDE_TIMEOUT_SLOW = int(os.environ.get("CLAUDE_TIMEOUT_SLOW_SECONDS", "3600"))
L1_RECENT_N = int(os.environ.get("L1_RECENT_N", "20"))

INBOX_ROOT = REPO_ROOT / "media" / "inbox" / "line"
RUNS_ROOT = REPO_ROOT / "data" / "line" / "runs"
ACTIVE_INDEX = RUNS_ROOT / "_active.json"
MCP_CONFIG = Path(__file__).parent / "mcp-config-line.json"

LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_BASE = "https://api-data.line.me/v2/bot"

# slow-command patterns: bump timeout, send pre-ack via reply_token, final result goes via push.
SLOW_PATTERNS = [
    re.compile(r"/weekly-plan", re.I),
    re.compile(r"/publish-from-plan", re.I),
    re.compile(r"/draft-post", re.I),
    re.compile(r"/publish-now", re.I),
    re.compile(r"weekly\s*plan", re.I),
    re.compile(r"週計[劃畫]"),
    re.compile(r"周计[劃划]"),
]

# In-process state: target_id → {"run_id": ..., "started_at": ...} for currently-running tasks.
RUNNING: dict[str, dict] = {}


def is_slow(text: str) -> bool:
    return any(p.search(text) for p in SLOW_PATTERNS)


# ---------- helpers ----------

def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def _new_run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:4]}"


def verify_signature(body: bytes, signature: str) -> bool:
    if not signature or not CHANNEL_SECRET:
        return False
    expected = base64.b64encode(
        hmac.new(CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)


def extract_target_id(source: dict) -> tuple[str, str]:
    """Return (target_id, source_type). target_id is one of group/room/user."""
    t = source.get("type", "user")
    if t == "group":
        return source.get("groupId", ""), "group"
    if t == "room":
        return source.get("roomId", ""), "room"
    return source.get("userId", ""), "user"


async def download_content(message_id: str, target_id: str, msg_type: str) -> str | None:
    """Download media from LINE content API and save to media/inbox/line/<target>/<message_id>.<ext>."""
    ext_map = {"image": "jpg", "video": "mp4", "audio": "m4a", "file": "bin"}
    ext = ext_map.get(msg_type, "bin")
    target_dir = INBOX_ROOT / memory._safe_id(target_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{message_id}.{ext}"

    if out_path.exists() and out_path.stat().st_size > 0:
        return str(out_path)

    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    url = f"{LINE_DATA_BASE}/message/{message_id}/content"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url, headers=headers)
        if r.status_code != 200:
            _log(f"download_content failed: {r.status_code} {r.text[:200]}")
            return None
        out_path.write_bytes(r.content)
        return str(out_path)
    except Exception as e:
        _log(f"download_content exception: {e}")
        return None


def build_prompt(
    target_id: str,
    source_type: str,
    user_id: str,
    payload_text: str,
    media_path: str | None,
    msg_type: str,
    slow: bool,
    run_id: str,
) -> str:
    """Build prompt prefix: L2 memory + L1 conversation + current message."""
    l2 = memory.read_memory(target_id) or "(none)"
    recent = memory.recent_messages(target_id, n=L1_RECENT_N)
    l1 = memory.format_recent_for_prompt(recent[:-1])  # exclude the current message just appended

    media_block = ""
    if media_path:
        media_block = f"\n[Current message attachment]\nType: {msg_type}\nLocal path: {media_path}\n"

    user_block = f"[Current message]\nSender: {user_id or 'unknown'}\nContent: {payload_text}\n"

    slow_note = ""
    if slow:
        slow_note = (
            "\nNote: this is a SLOW command. The webhook has already sent an ack to the user via "
            "reply_token, so your `line_send` will go via push (consumes 1 push quota). Send "
            "exactly 1 `line_send` with the final result when done.\n"
        )

    return f"""You are handling a message for a LINE {source_type} ({target_id}).
Run ID: {run_id} — your progress is being streamed to data/line/runs/{run_id}/summary.log

---
[Group long-term preferences / data/line/memory/{memory._safe_id(target_id)}.md]
{l2}

---
[Recent conversation history — last {L1_RECENT_N} messages from L1 buffer]
{l1}
---
{media_block}{user_block}
---
Operating rules:
1. Before starting, read `CLAUDE.md` + `docs/OPERATING_RULES.md` + **`bridge/line/RULES.md`** (the last file overrides TG-specific parts of OPERATING_RULES).
2. All replies to the user must go through `mcp__line__line_send` (always prefer reply, free and unlimited). stdout is NOT pushed back to LINE — no line_send = user sees nothing.
3. **Send exactly 1 message per user message** — wait until the task is fully complete, then call `line_send` once with the final result. **Do not send a "processing..." message** (it would waste the only reply token).
4. **Fail fast OR ask — never experiment.** Default disposition is stop-and-surface, not "try to fix" or "pick most likely interpretation". Token cost of asking ≪ token cost of running the wrong task.
   - **On error** (tool returns `is_error: true`, subagent reports failure, MCP error, login expired, 2FA, paywall): call `line_send` ONCE with `❌ <step>\nerror: <verbatim>\nrun: {run_id}` and STOP. Do not try another approach, do not respawn the subagent, do not silently swap platforms.
   - **On uncertainty** (ambiguous instruction, missing parameter, two valid interpretations, vague reference like "上次那個", you're about to make up a value or pick one of N without a stated reason): call `line_send` ONCE with `❓ <unclear bit>\noptions:\n- A) ...\n- B) ...\nrun: {run_id}` and STOP. Do not guess, do not run "safest default", do not run both options.
   - Cheap retries inside a single MCP call (one Playwright re-click on a slow page) are still fine per OPERATING_RULES §5. The bar for stopping is "I'm not ≥ 90% sure" — anything below that → ask.
5. Things worth remembering long-term (brand preferences, rules, client habits) → write to `data/line/memory/{memory._safe_id(target_id)}.md` via Edit tool; automatically included next time.{slow_note}
"""


def write_mcp_config():
    """Ensure mcp-config-line.json exists; points to local line_mcp_server.py + playwright."""
    cfg = {
        "mcpServers": {
            "line": {
                "command": sys.executable,
                "args": [str(Path(__file__).parent / "line_mcp_server.py")],
            },
            "playwright": {
                "command": "npx",
                "args": [
                    "-y",
                    "@playwright/mcp@latest",
                    "--user-data-dir",
                    str(REPO_ROOT / "browser_profiles"),
                    "--allow-unrestricted-file-access",
                ],
            },
        }
    }
    if not MCP_CONFIG.exists():
        MCP_CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


# ---------- direct LINE API (pre-ack, concurrency-reject, error-push) ----------

async def _line_post(path: str, payload: dict) -> tuple[int, str]:
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{LINE_API_BASE}{path}", headers=headers, json=payload)
    return r.status_code, r.text


async def line_reply_direct(reply_token: str, text: str) -> bool:
    if not reply_token:
        return False
    status, body = await _line_post(
        "/message/reply",
        {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
    )
    if status != 200:
        _log(f"line_reply failed {status} {body[:200]}")
        return False
    return True


async def line_push_direct(target_id: str, text: str) -> bool:
    if not target_id:
        return False
    status, body = await _line_post(
        "/message/push",
        {"to": target_id, "messages": [{"type": "text", "text": text}]},
    )
    if status != 200:
        _log(f"line_push failed {status} {body[:200]}")
        return False
    return True


# ---------- stream-json event → human-readable summary ----------

def _short(v, n: int = 60) -> str:
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _summarize_event(ev: dict) -> str | None:
    """Turn one stream-json event into a one-line summary for summary.log.
    Return None for events not worth logging."""
    et = ev.get("type")
    if et == "system":
        sub = ev.get("subtype", "")
        if sub == "init":
            sid = (ev.get("session_id") or "")[:8]
            model = ev.get("model") or "?"
            cwd = ev.get("cwd") or ""
            return f"[system/init] session={sid} model={model} cwd={cwd}"
        return f"[system/{sub}]"
    if et == "assistant":
        msg = ev.get("message") or {}
        blocks = msg.get("content") or []
        parts = []
        for b in blocks:
            btype = b.get("type")
            if btype == "text":
                txt = (b.get("text") or "").strip()
                if txt:
                    parts.append(f"text={_short(txt, 200)}")
            elif btype == "tool_use":
                name = b.get("name", "?")
                inp = b.get("input") or {}
                args = ", ".join(f"{k}={_short(v, 50)}" for k, v in list(inp.items())[:3])
                parts.append(f"TOOL {name}({args})")
            elif btype == "thinking":
                parts.append("thinking")
        if not parts:
            return None
        return "[asst] " + " | ".join(parts)
    if et == "user":
        msg = ev.get("message") or {}
        blocks = msg.get("content") or []
        parts = []
        for b in blocks:
            if b.get("type") == "tool_result":
                content = b.get("content")
                if isinstance(content, list):
                    snippets = []
                    for c in content[:2]:
                        if isinstance(c, dict) and c.get("type") == "text":
                            snippets.append(_short(c.get("text") or "", 120))
                    txt = " ".join(snippets)
                elif isinstance(content, str):
                    txt = _short(content, 120)
                else:
                    txt = ""
                marker = "ERR" if b.get("is_error") else "ok"
                parts.append(f"tool_result({marker}) {txt}")
        if not parts:
            return None
        return "[user] " + " | ".join(parts)
    if et == "result":
        sub = ev.get("subtype", "")
        dur = ev.get("duration_ms")
        cost = ev.get("total_cost_usd")
        usage = ev.get("usage") or {}
        toks_in = usage.get("input_tokens")
        toks_out = usage.get("output_tokens")
        return f"[RESULT/{sub}] duration={dur}ms tokens_in={toks_in} tokens_out={toks_out} cost=${cost}"
    return f"[{et}] {_short(ev, 200)}"


# ---------- run metadata + active index ----------

def _write_meta(run_dir: Path, **fields):
    meta_file = run_dir / "meta.json"
    existing = {}
    if meta_file.exists():
        try:
            existing = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(fields)
    meta_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def _update_active_index(target_id: str, run_id: str | None):
    """Maintain data/line/runs/_active.json mapping currently-running target_id → run_id."""
    ACTIVE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    try:
        idx = json.loads(ACTIVE_INDEX.read_text(encoding="utf-8")) if ACTIVE_INDEX.exists() else {}
    except Exception:
        idx = {}
    if run_id is None:
        idx.pop(target_id, None)
    else:
        idx[target_id] = {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat()}
    ACTIVE_INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------- spawn with streaming ----------

async def spawn_claude_streaming(
    prompt: str,
    target_id: str,
    user_id: str,
    reply_token: str,
    run_dir: Path,
    timeout: int,
    reply_token_pre_used: bool,
) -> tuple[int, str, str]:
    """Spawn `claude -p` with stream-json output. Stream events to run_dir/* in real time.
    Returns (rc, final_text_from_result_event, stderr_text)."""
    write_mcp_config()

    flag_dir = Path(tempfile.gettempdir()) / "sma-line-reply-flags"
    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_file = flag_dir / f"{uuid.uuid4().hex}.used"
    if reply_token_pre_used:
        # pre-mark: tell line_mcp_server.line_send to skip reply and go straight to push.
        flag_file.touch()

    env = {
        **os.environ,
        "LINE_CHANNEL_ACCESS_TOKEN": CHANNEL_ACCESS_TOKEN,
        "LINE_TARGET_ID": target_id,
        "LINE_REPLY_TOKEN": reply_token,
        "LINE_USER_ID": user_id,
        "LINE_REPLY_TOKEN_USED_FILE": str(flag_file),
        "LINE_RUN_ID": run_dir.name,
    }

    cmd = [
        CLAUDE_BIN,
        "-p", prompt,
        "--mcp-config", str(MCP_CONFIG),
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
    ]

    events_file = run_dir / "events.jsonl"
    summary_file = run_dir / "summary.log"
    stderr_file = run_dir / "stderr.log"

    _log(
        f"spawn run={run_dir.name} target={target_id[:8]} "
        f"timeout={timeout}s pre_acked={reply_token_pre_used}"
    )

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    final_text = ""
    final_err_chunks: list[str] = []

    async def consume_stdout():
        nonlocal final_text
        ef = events_file.open("ab")
        sf = summary_file.open("a", encoding="utf-8")
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                ef.write(line)
                ef.flush()
                try:
                    ev = json.loads(line.decode("utf-8", errors="replace"))
                except Exception:
                    sf.write(f"{datetime.now().strftime('%H:%M:%S')} [raw] {line[:200]!r}\n")
                    sf.flush()
                    continue
                if ev.get("type") == "result":
                    final_text = (ev.get("result") or "").strip()
                summary = _summarize_event(ev)
                if summary:
                    sf.write(f"{datetime.now().strftime('%H:%M:%S')} {summary}\n")
                    sf.flush()
        finally:
            ef.close()
            sf.close()

    async def consume_stderr():
        f = stderr_file.open("ab")
        try:
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                f.write(line)
                f.flush()
                final_err_chunks.append(line.decode("utf-8", errors="replace"))
        finally:
            f.close()

    try:
        try:
            await asyncio.wait_for(
                asyncio.gather(consume_stdout(), consume_stderr(), proc.wait()),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            _log(f"TIMEOUT run={run_dir.name} after {timeout}s — killing")
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
            return -1, final_text, "".join(final_err_chunks) + f"\n[webhook] killed after {timeout}s"

        rc = proc.returncode or 0
        return rc, final_text, "".join(final_err_chunks)
    finally:
        try:
            flag_file.unlink(missing_ok=True)
        except Exception:
            pass


# ---------- event handler ----------

async def handle_message_event(event: dict):
    msg = event.get("message", {})
    msg_type = msg.get("type", "")
    msg_id = msg.get("id", "")
    reply_token = event.get("replyToken", "")
    source = event.get("source", {})
    target_id, source_type = extract_target_id(source)
    user_id = source.get("userId", "")

    if not target_id:
        _log(f"skipping event without target id: {event}")
        return

    # extract message text / media
    text = ""
    media_path: str | None = None
    if msg_type == "text":
        text = msg.get("text", "")
    elif msg_type in ("image", "video", "audio", "file"):
        media_path = await download_content(msg_id, target_id, msg_type)
        text = f"[{msg_type}]"
        if msg.get("fileName"):
            text += f" {msg['fileName']}"
    else:
        text = f"[{msg_type}]"

    # L1: always write (even if skipped by group filter)
    memory.append_message(
        target_id, role="user", text=text, user_id=user_id,
        media_path=media_path, msg_type=msg_type,
    )

    # group filter
    do_respond, payload = should_respond(source_type, text, GROUP_PREFIXES)
    if not do_respond:
        _log(f"silent ignore (no prefix in {source_type}): {target_id[:8]}")
        return

    payload = payload or text

    # concurrency guard: only one claude -p per target_id at a time.
    if target_id in RUNNING:
        active = RUNNING[target_id]
        elapsed = (datetime.now() - active["started_at"]).total_seconds()
        await line_reply_direct(
            reply_token,
            f"⏳ 上一個任務還在跑(run={active['run_id']},已 {int(elapsed)}s),請等它完成。\n"
            f"查看進度: tail -f data/line/runs/{active['run_id']}/summary.log\n"
            f"取消: 用 /unlock-run {active['run_id']}(尚未實作 → 手動 kill webhook_server)"
        )
        _log(f"concurrency reject for {target_id[:8]} (active={active['run_id']})")
        return

    slow = is_slow(payload)
    timeout = CLAUDE_TIMEOUT_SLOW if slow else CLAUDE_TIMEOUT

    run_id = _new_run_id()
    run_dir = RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(
        target_id, source_type, user_id, payload, media_path, msg_type,
        slow=slow, run_id=run_id,
    )
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    _write_meta(
        run_dir,
        run_id=run_id,
        target_id=target_id,
        source_type=source_type,
        user_id=user_id,
        message=payload[:500],
        slow=slow,
        timeout_seconds=timeout,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="running",
    )

    # For slow commands, consume reply_token immediately with an ack so the agent isn't
    # racing the 30-second window. Final result will go via push.
    reply_token_pre_used = False
    if slow:
        ack = (
            f"📅 收到慢任務(run={run_id})\n"
            f"預估 5–30 分鐘,完成後 push 結果。\n"
            f"進度: data/line/runs/{run_id}/summary.log"
        )
        if await line_reply_direct(reply_token, ack):
            reply_token_pre_used = True
            _log(f"slow pre-ack sent run={run_id}")
        else:
            _log(f"slow pre-ack FAILED run={run_id} — agent will race the 30s reply window")

    RUNNING[target_id] = {"run_id": run_id, "started_at": datetime.now()}
    _update_active_index(target_id, run_id)

    try:
        rc, final_text, stderr = await spawn_claude_streaming(
            prompt=prompt,
            target_id=target_id,
            user_id=user_id,
            reply_token=reply_token,
            run_dir=run_dir,
            timeout=timeout,
            reply_token_pre_used=reply_token_pre_used,
        )
    finally:
        RUNNING.pop(target_id, None)
        _update_active_index(target_id, None)

    status = "ok" if rc == 0 else ("timeout" if rc == -1 else "error")
    _write_meta(
        run_dir,
        rc=rc,
        finished_at=datetime.now(timezone.utc).isoformat(),
        status=status,
        final_text_len=len(final_text or ""),
        stderr_tail=stderr[-2000:] if stderr else "",
    )

    summary = (final_text or "").strip() or "(no result event)"
    if rc != 0:
        # If Claude didn't deliver a final line_send (e.g. timeout), push the error so the user
        # isn't left wondering. For successful runs, Claude is responsible for line_send.
        err_text = (stderr or "")[-400:].strip()
        notice = f"❌ 任務失敗(run={run_id}, rc={rc})\n{summary[:200]}\nstderr tail: {err_text}"
        await line_push_direct(target_id, notice)
        summary = f"[claude rc={rc}] {summary[:500]}"

    memory.append_message(target_id, role="assistant", text=summary[:2000])

    if rc != 0:
        _log(f"FAILED rc={rc} run={run_id} stderr={stderr[-300:]!r}")
    else:
        _log(f"done rc=0 run={run_id} final_len={len(final_text or '')}")


async def handle_event(event: dict):
    try:
        et = event.get("type", "")
        if et == "message":
            await handle_message_event(event)
        elif et in ("follow", "join"):
            _log(f"event: {et} from {event.get('source', {})}")
            # optional: send welcome message (future work)
        else:
            _log(f"unhandled event type: {et}")
    except Exception as e:
        _log(f"event handler exception: {e!r}")


# ---------- FastAPI ----------

app = FastAPI(title="social-media-agent LINE webhook")


@app.get("/healthz")
async def healthz():
    active = {}
    try:
        if ACTIVE_INDEX.exists():
            active = json.loads(ACTIVE_INDEX.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "active_runs": active,
    }


@app.get("/runs")
async def runs(limit: int = 20):
    """List the N most recent runs with their meta.json contents."""
    if not RUNS_ROOT.exists():
        return {"runs": []}
    dirs = sorted(
        [d for d in RUNS_ROOT.iterdir() if d.is_dir() and not d.name.startswith("_")],
        key=lambda d: d.name,
        reverse=True,
    )[:limit]
    out = []
    for d in dirs:
        meta = {}
        try:
            mf = d / "meta.json"
            if mf.exists():
                meta = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            pass
        out.append({"run_id": d.name, **meta})
    return {"runs": out}


@app.post("/webhook")
async def webhook(req: Request, x_line_signature: str = Header(None)):
    body = await req.body()
    if not verify_signature(body, x_line_signature or ""):
        raise HTTPException(status_code=403, detail="invalid signature")

    payload = json.loads(body)
    events = payload.get("events", [])
    _log(f"webhook: {len(events)} event(s)")

    # don't block LINE's webhook timeout (must return 200 within ~1s)
    for ev in events:
        asyncio.create_task(handle_event(ev))

    return {"ok": True}


def main():
    import uvicorn

    if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
        _log("ERROR: LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN not set.")
        _log(f"Fill them in {Path(__file__).parent / '.env'} before starting.")
        sys.exit(1)

    if not shutil.which(CLAUDE_BIN):
        _log(f"ERROR: claude CLI not found (CLAUDE_BIN={CLAUDE_BIN})."
             f" Set CLAUDE_BIN to an absolute path in .env (output of `which claude`).")
        sys.exit(1)

    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    # Clear stale active index on boot — anything left over is from a prior crashed process.
    if ACTIVE_INDEX.exists():
        try:
            ACTIVE_INDEX.unlink()
        except Exception:
            pass

    write_mcp_config()
    _log(f"listening on http://{WEBHOOK_HOST}:{WEBHOOK_PORT}")
    _log(f"prefixes for group/room: {GROUP_PREFIXES}")
    _log(f"claude bin: {CLAUDE_BIN}, timeout: {CLAUDE_TIMEOUT}s (slow: {CLAUDE_TIMEOUT_SLOW}s)")
    _log(f"runs root: {RUNS_ROOT}")

    uvicorn.run(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT, log_level="info")


if __name__ == "__main__":
    main()
