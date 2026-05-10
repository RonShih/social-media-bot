---
name: local-writer
description: Save a generated or uploaded asset (image / video) into media/assets/<brand>/.
---

> Common rules: `docs/OPERATING_RULES.md`.

## save_asset

Input:
- `name`: filename or relative path under the brand's `assets_dir` (e.g. `unboxing/2026-05-09.jpg`, `inbox/abc.mp4`).
- One of:
  - `base64`: base64-encoded bytes.
  - `source_url`: URL to download.

Steps:
- Resolve `<repo>/media/assets/<brand>/<name>`. `mkdir -p` the parent.
- If `base64`: `echo <base64> | base64 -d > <abs path>`.
- If `source_url`: `curl -sL --max-time 60 -o <abs path> <url>`.

Output:
```json
{ "path": "media/assets/<brand>/<name>", "abs_path": "/abs/.../media/assets/<brand>/<name>", "size_bytes": 123456 }
```

## Failure handling

- Disk full → `{ "error": "disk full" }`
- Source URL fails → `{ "error": "source_url fetch failed: <http_code|reason>" }`
- Path traversal (`..` outside `media/assets/<brand>/`) → `{ "error": "invalid path" }`

Always return structured JSON; never throw.
