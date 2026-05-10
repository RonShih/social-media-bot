---
name: local-reader
description: Resolve local asset paths and list the brand asset library. Used by publish-* and weekly-plan-* before they touch files.
---

> Common rules: `docs/OPERATING_RULES.md`. Brand context: `config/brands/<active>.yaml` (active brand from `config/active-brand` or `BRAND` env).

## Two modes

### 1. resolve_asset_path

Given a relative or absolute path, return its absolute form and confirm it exists. `publish-*` skills must call this before sending a file path to Playwright.

Input: `path` (relative to repo root, absolute, or `~/.claude/channels/telegram/inbox/...`).

Output:
```json
{ "abs_path": "/abs/.../media/assets/<brand>/...", "exists": true, "size_bytes": 123456, "kind": "image|video|other" }
```

Not found:
```json
{ "error": "asset not found", "path": "..." }
```

`kind` heuristic: extension `.jpg|.jpeg|.png|.webp|.gif` → `image`; `.mp4|.mov|.webm|.mkv` → `video`; else `other`.

### 2. list_assets

List files in the brand's asset library or a Telegram inbox folder.

Input: `dir` (optional). If omitted, lists both `media/assets/<brand>/` and `~/.claude/channels/telegram/inbox/`.

Output: array of `{ name, abs_path, size_bytes, modified_at, kind }`.

## Don'ts

- No download, no transcode, no resize.
- No caching — `stat` every call.
- Do not accept a path outside the repo or `~/.claude/channels/telegram/inbox/` (security guard).
