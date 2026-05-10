"""LINE webhook server.

Receives LINE webhooks → verify signature → download media → inject memory → spawn `claude -p` headless.
Claude replies to LINE via tools exposed by line_mcp_server.

Start:
    cd <repo>
    python bridge/line/webhook_server.py
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
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
L1_RECENT_N = int(os.environ.get("L1_RECENT_N", "20"))

INBOX_ROOT = REPO_ROOT / "media" / "inbox" / "line"
MCP_CONFIG = Path(__file__).parent / "mcp-config-line.json"

LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_BASE = "https://api-data.line.me/v2/bot"


# ---------- helpers ----------

def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


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
) -> str:
    """Build prompt prefix: L2 memory + L1 conversation + current message."""
    l2 = memory.read_memory(target_id) or "(none)"
    recent = memory.recent_messages(target_id, n=L1_RECENT_N)
    l1 = memory.format_recent_for_prompt(recent[:-1])  # exclude the current message just appended

    media_block = ""
    if media_path:
        media_block = f"\n[Current message attachment]\nType: {msg_type}\nLocal path: {media_path}\n"

    user_block = f"[Current message]\nSender: {user_id or 'unknown'}\nContent: {payload_text}\n"

    return f"""You are handling a message for a LINE {source_type} ({target_id}).

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
4. Things worth remembering long-term (brand preferences, rules, client habits) → write to `data/line/memory/{memory._safe_id(target_id)}.md` via Edit tool; automatically included next time.
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


async def spawn_claude(
    prompt: str,
    target_id: str,
    user_id: str,
    reply_token: str,
) -> tuple[int, str, str]:
    """Spawn `claude -p` and return (returncode, stdout, stderr)."""
    write_mcp_config()

    # one-time reply-token-used flag file
    flag_dir = Path(tempfile.gettempdir()) / "sma-line-reply-flags"
    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_file = flag_dir / f"{uuid.uuid4().hex}.used"

    env = {
        **os.environ,
        "LINE_CHANNEL_ACCESS_TOKEN": CHANNEL_ACCESS_TOKEN,
        "LINE_TARGET_ID": target_id,
        "LINE_REPLY_TOKEN": reply_token,
        "LINE_USER_ID": user_id,
        "LINE_REPLY_TOKEN_USED_FILE": str(flag_file),
    }

    cmd = [
        CLAUDE_BIN,
        "-p", prompt,
        "--mcp-config", str(MCP_CONFIG),
        "--dangerously-skip-permissions",
    ]

    _log(f"spawning claude (target={target_id[:8]}, prompt_len={len(prompt)})")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=CLAUDE_TIMEOUT
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return -1, "", f"claude timeout after {CLAUDE_TIMEOUT}s"

        return (
            proc.returncode or 0,
            (stdout_b or b"").decode("utf-8", errors="replace"),
            (stderr_b or b"").decode("utf-8", errors="replace"),
        )
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
        # sticker / location etc. treated as text hint for now
        text = f"[{msg_type}]"

    # L1: always write (even if skipped by group filter, context is available next time bot is mentioned)
    memory.append_message(
        target_id,
        role="user",
        text=text,
        user_id=user_id,
        media_path=media_path,
        msg_type=msg_type,
    )

    # group filter
    do_respond, payload = should_respond(source_type, text, GROUP_PREFIXES)
    if not do_respond:
        _log(f"silent ignore (no prefix in {source_type}): {target_id[:8]}")
        return

    payload = payload or text
    prompt = build_prompt(target_id, source_type, user_id, payload, media_path, msg_type)

    rc, stdout, stderr = await spawn_claude(prompt, target_id, user_id, reply_token)

    # write Claude's final stdout back to L1 buffer as assistant message (even if empty)
    summary = (stdout or "").strip() or "(no stdout)"
    if rc != 0:
        summary = f"[claude rc={rc}] {summary[:500]}"
    memory.append_message(target_id, role="assistant", text=summary[:2000])

    if rc != 0:
        _log(f"claude failed rc={rc} stderr={stderr[:500]}")


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
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


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

    write_mcp_config()
    _log(f"listening on http://{WEBHOOK_HOST}:{WEBHOOK_PORT}")
    _log(f"prefixes for group/room: {GROUP_PREFIXES}")
    _log(f"claude bin: {CLAUDE_BIN}, timeout: {CLAUDE_TIMEOUT}s")

    uvicorn.run(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT, log_level="info")


if __name__ == "__main__":
    main()
