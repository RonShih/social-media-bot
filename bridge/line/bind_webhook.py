#!/usr/bin/env python3
"""Bind a webhook URL to a LINE Messaging API channel.

Usage:
  # 1. Provide URL directly (recommended)
  python bridge/line/bind_webhook.py https://abc.lhr.life
  python bridge/line/bind_webhook.py https://line.example.com/webhook

  # 2. No URL → auto-detect ngrok local API (http://127.0.0.1:4040)
  python bridge/line/bind_webhook.py

  # 3. Show current setting only
  python bridge/line/bind_webhook.py --show

Flow:
  1. PUT  /v2/bot/channel/webhook/endpoint   set new URL
  2. POST /v2/bot/channel/webhook/test       trigger LINE to make a real test request (expect 200)
  3. GET  /v2/bot/channel/webhook/endpoint   confirm active=true

LINE API ref: https://developers.line.biz/en/reference/messaging-api/#set-webhook-endpoint-url
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
API = "https://api.line.me/v2/bot/channel/webhook"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _normalize_url(url: str) -> str:
    """Ensure URL ends with /webhook (the path used by webhook_server.py)."""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if url.startswith("http://"):
        print("⚠️  LINE only accepts https:// webhook URLs", file=sys.stderr)
    if not url.endswith("/webhook"):
        url = url + "/webhook"
    return url


def detect_ngrok_url() -> str | None:
    """Try to get public_url from the ngrok local API."""
    try:
        r = httpx.get("http://127.0.0.1:4040/api/tunnels", timeout=2.0)
        if r.status_code != 200:
            return None
        tunnels = r.json().get("tunnels", [])
        for t in tunnels:
            url = t.get("public_url", "")
            if url.startswith("https://"):
                return url
        return None
    except Exception:
        return None


def get_current() -> dict:
    r = httpx.get(f"{API}/endpoint", headers=_headers(), timeout=10.0)
    return {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text}


def set_endpoint(url: str) -> dict:
    r = httpx.put(
        f"{API}/endpoint",
        headers=_headers(),
        json={"endpoint": url},
        timeout=10.0,
    )
    return {"status": r.status_code, "body": r.json() if r.text else {}}


def test_endpoint() -> dict:
    """Trigger LINE to make a test request to the webhook endpoint."""
    r = httpx.post(f"{API}/test", headers=_headers(), timeout=15.0)
    try:
        return {"status": r.status_code, "body": r.json()}
    except Exception:
        return {"status": r.status_code, "body": r.text}


def main():
    if not ACCESS_TOKEN:
        print(f"ERROR: LINE_CHANNEL_ACCESS_TOKEN not set (check {ENV_PATH})", file=sys.stderr)
        sys.exit(2)

    args = sys.argv[1:]

    if "--show" in args:
        cur = get_current()
        print(json.dumps(cur, ensure_ascii=False, indent=2))
        return

    if args and args[0] not in ("-h", "--help"):
        url = _normalize_url(args[0])
    else:
        if args and args[0] in ("-h", "--help"):
            print(__doc__)
            return
        detected = detect_ngrok_url()
        if not detected:
            print("ERROR: No URL provided and ngrok not detected.", file=sys.stderr)
            print("  Usage: python bridge/line/bind_webhook.py <https://your-tunnel-url>", file=sys.stderr)
            sys.exit(2)
        url = _normalize_url(detected)
        print(f"🔍 Detected from ngrok: {url}")

    # 1. PUT
    print(f"📌 Setting webhook URL → {url}")
    r1 = set_endpoint(url)
    if r1["status"] != 200:
        print(f"❌ PUT failed: {r1}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ PUT 200")

    # 2. test
    print(f"🧪 Triggering LINE webhook test...")
    r2 = test_endpoint()
    body = r2.get("body", {})
    if r2["status"] == 200 and isinstance(body, dict) and body.get("success"):
        print(f"✅ test 200 — webhook is live")
        print(f"   reason: {body.get('reason', '?')}, status code from server: {body.get('statusCode', '?')}")
    else:
        print(f"⚠️  test result: {json.dumps(body, ensure_ascii=False)}")
        print(f"   Common causes: webhook_server.py not running / tunnel not connected / signature error")

    # 3. confirm active
    cur = get_current()
    print(f"📋 Current status: {json.dumps(cur['body'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
