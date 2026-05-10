"""Group message prefix filter.

In LINE groups, the bot receives all messages by default; spawning Claude unconditionally would be too costly.
Rules:
  - 1:1 (source.type == 'user')      → always process
  - group / room                      → only process when message starts with a prefix
  - Regardless of whether processed, the L1 buffer is always written (context is available next time bot is mentioned)
"""

from __future__ import annotations


def parse_prefixes(env_value: str | None) -> list[str]:
    if not env_value:
        return ["@editor", "/sma"]
    return [p.strip() for p in env_value.split(",") if p.strip()]


def should_respond(
    source_type: str,
    text: str,
    prefixes: list[str],
) -> tuple[bool, str | None]:
    """Return (should_respond, message text with prefix stripped — only set when responding)."""
    if source_type == "user":
        return True, text

    if source_type not in ("group", "room"):
        # Unknown source types: ignore conservatively
        return False, None

    stripped = text.lstrip()
    for p in prefixes:
        if stripped.startswith(p):
            payload = stripped[len(p):].lstrip(" :,，。、")
            return True, payload

    return False, None
