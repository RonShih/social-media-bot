"""Memory layer helpers.

L1 conversation buffer  — data/line/conversations/<group_id>.jsonl     append-only
L2 structured preferences  — data/line/memory/<group_id>.md            Claude edits via Edit tool
L3 content history   — data/posts.db (SQLite, connected in Phase 2)
L4 weekly/monthly digest — data/line/digests/<group_id>-<period>.md       Phase 3 cron-generated

This file currently only implements L1 + L2 read (for prompt injection). L2 writes are handled by Claude via the Edit tool.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data" / "line"
CONV_DIR = DATA_ROOT / "conversations"
MEMORY_DIR = DATA_ROOT / "memory"
DIGEST_DIR = DATA_ROOT / "digests"


def _safe_id(raw: str) -> str:
    """LINE ids are [A-Za-z0-9] and theoretically need no sanitization; strip path characters as a safety measure."""
    return "".join(c for c in raw if c.isalnum() or c in "-_") or "unknown"


def conv_path(target_id: str) -> Path:
    return CONV_DIR / f"{_safe_id(target_id)}.jsonl"


def memory_path(target_id: str) -> Path:
    return MEMORY_DIR / f"{_safe_id(target_id)}.md"


def append_message(
    target_id: str,
    role: str,           # "user" | "assistant" | "system"
    text: str,
    *,
    user_id: str | None = None,
    media_path: str | None = None,
    msg_type: str = "text",
):
    """L1: append a single message line to the group's jsonl."""
    CONV_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "role": role,
        "user_id": user_id,
        "type": msg_type,
        "text": text,
    }
    if media_path:
        record["media_path"] = media_path
    with conv_path(target_id).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def recent_messages(target_id: str, n: int = 20) -> list[dict]:
    """L1: read the most recent n messages. Returns empty list if file does not exist."""
    p = conv_path(target_id)
    if not p.exists():
        return []
    # Simple implementation: read all lines then take the last N. jsonl grows slowly, no need for reverse iter.
    with p.open(encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def read_memory(target_id: str) -> str:
    """L2: read the memory.md for this group. Returns empty string if file does not exist."""
    p = memory_path(target_id)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()


def ensure_memory_file(target_id: str) -> Path:
    """Ensure the L2 memory.md exists (required before Claude's first Edit call)."""
    p = memory_path(target_id)
    if not p.exists():
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        p.write_text(
            f"# Memory — {target_id}\n\n"
            "(Accumulated preferences, rules, and learned facts for this group / 1:1 chat."
            " Agent maintains this file via the Edit tool. One entry per line, e.g.: \"brand color: green\" \"avoid excessive emoji\".)"
            "\n\n",
            encoding="utf-8",
        )
    return p


def format_recent_for_prompt(messages: list[dict]) -> str:
    """Format L1 message list into a prompt section."""
    if not messages:
        return "(none)"
    lines = []
    for m in messages:
        ts = m.get("ts", "?")
        role = m.get("role", "?")
        uid = m.get("user_id")
        prefix = f"[{ts}] {role}"
        if uid and role == "user":
            prefix += f" ({uid[:8]}...)"
        text = m.get("text", "")
        if m.get("media_path"):
            text = f"{text} <media: {Path(m['media_path']).name}>"
        # Truncate if too long
        if len(text) > 500:
            text = text[:500] + "…"
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines)
