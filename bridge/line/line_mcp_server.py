#!/usr/bin/env python3
"""LINE MCP server (stdio).

Started alongside `claude -p` by webhook_server.py.
Receives reply_token / target_id via env, allowing Claude to call tools that reply to LINE directly.

Tools:
  line_reply(text)        — reply via reply_token, must be used within 30s, only once per session
  line_push(text)         — push via push API (used after reply_token is consumed)
  line_send(text)         — auto: uses reply_token if unused, otherwise push
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types


CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
TARGET_ID = os.environ.get("LINE_TARGET_ID", "")
REPLY_TOKEN = os.environ.get("LINE_REPLY_TOKEN", "")
USED_FLAG_FILE = os.environ.get("LINE_REPLY_TOKEN_USED_FILE", "")

LINE_API_BASE = "https://api.line.me/v2/bot"

server = Server("line-bot")


def _log(msg: str):
    print(f"[line_mcp] {msg}", file=sys.stderr, flush=True)


def _reply_token_used() -> bool:
    return bool(USED_FLAG_FILE) and Path(USED_FLAG_FILE).exists()


def _mark_reply_token_used():
    if USED_FLAG_FILE:
        Path(USED_FLAG_FILE).touch()


async def _call_line(path: str, payload: dict) -> tuple[int, str]:
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{LINE_API_BASE}{path}", headers=headers, json=payload)
    return r.status_code, r.text


async def _do_reply(text: str) -> tuple[bool, str]:
    if not REPLY_TOKEN:
        return False, "no reply_token in env"
    status, body = await _call_line(
        "/message/reply",
        {"replyToken": REPLY_TOKEN, "messages": [{"type": "text", "text": text}]},
    )
    if status == 200:
        _mark_reply_token_used()
        return True, "ok"
    return False, f"reply failed: {status} {body}"


async def _do_push(text: str) -> tuple[bool, str]:
    if not TARGET_ID:
        return False, "no target_id in env"
    status, body = await _call_line(
        "/message/push",
        {"to": TARGET_ID, "messages": [{"type": "text", "text": text}]},
    )
    if status == 200:
        return True, "ok"
    return False, f"push failed: {status} {body}"


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    common_text_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Plain text message (LINE does not render markdown — avoid *bold* / `code` / tables)",
            }
        },
        "required": ["text"],
    }
    return [
        types.Tool(
            name="line_send",
            description=(
                "Send a plain text message to LINE. Automatically chooses reply_token (if unused) or push."
                " **Use this in 99% of cases.**"
            ),
            inputSchema=common_text_schema,
        ),
        types.Tool(
            name="line_reply",
            description=(
                "Force use of reply_token (usable only once, within 30s)."
                " Returns error if token already used — use line_send in general."
            ),
            inputSchema=common_text_schema,
        ),
        types.Tool(
            name="line_push",
            description=(
                "Force use of push API. Use when a task runs long or multiple messages are needed."
                " Free plan has a monthly quota (200 messages) — don't abuse."
            ),
            inputSchema=common_text_schema,
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    text = (arguments or {}).get("text", "").strip()
    if not text:
        return [types.TextContent(type="text", text='{"error":"text is required"}')]

    if name == "line_send":
        if _reply_token_used():
            ok, info = await _do_push(text)
            method = "push"
        else:
            ok, info = await _do_reply(text)
            if not ok:
                # reply failed (token expired, etc.) → fall back to push
                ok, info = await _do_push(text)
                method = "push (reply fallback)"
            else:
                method = "reply"
    elif name == "line_reply":
        ok, info = await _do_reply(text)
        method = "reply"
    elif name == "line_push":
        ok, info = await _do_push(text)
        method = "push"
    else:
        return [types.TextContent(type="text", text=f'{{"error":"unknown tool: {name}"}}')]

    result = {"ok": ok, "method": method, "info": info}
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main():
    _log(f"starting (target={TARGET_ID[:6] if TARGET_ID else 'none'}..., "
         f"reply_token={'set' if REPLY_TOKEN else 'none'})")
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
