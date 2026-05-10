# How to use

End-to-end walkthrough from fresh clone to weekly cadence.

## 1. Per-machine setup

```
cd /path/to/social-media-bot
cp .claude/settings.example.json .claude/settings.json
# edit the --user-data-dir absolute path inside .claude/settings.json

echo noirs-boxes > config/active-brand
npm install                 # installs exceljs (used by scripts/plan-*.mjs)
```

Sanity check:

```
node scripts/plan-export.mjs                # should error with usage text
ls -la config/brands/                       # _example.yaml + noirs-boxes.yaml
cat config/active-brand                     # noirs-boxes
```

## 2. Configure the brand

Either edit `config/brands/<slug>.yaml` directly, or run:

```
/setup
```

The `/setup` command walks through identity, voice, socials, products, themes, content style. Skip empty fields rather than inventing values.

## 3. First-time login

One Chromium window walks through every platform, you log in, sessions persist.

```
/first-time-login
```

You will see prompts: "Log into Facebook in the browser. Reply `ok` when done." Reply `ok` after each successful login. After all six platforms are done, the command closes Chromium and saves `browser_profiles/<brand>/`.

If a login session expires later, re-run `/first-time-login` (it can re-open just the platforms that need refresh — pass arg `facebook,instagram` if you want to limit, otherwise it does all six).

## 4. One-off post

Two-stage flow:

```
/draft-post fb,ig,x,threads
   # spawns subagents per platform; replies preview (plain text)

# review the preview
/publish-now draft:<id>
   # publishes sequentially; replies with post URLs
```

With a reference URL:

```
/draft-post fb,ig --url https://news.example.com/article
```

For video posts, attach the video first (TG: send the file; terminal: drop into `media/assets/<brand>/inbox/`), then:

```
/draft-post tt,yt,fb --mode video
```

## 5. Pre-flight check

Before running real publishes on a platform UI you haven't tested in a while:

```
/test-roundtrip threads --mode dry-run
   # walks the publish flow up to (but not including) the final Publish click
```

When you trust a flow and want to validate end-to-end including delete:

```
/test-roundtrip threads --mode roundtrip
   # publishes for real, captures URL, deletes via delete-threads, verifies removed
```

YouTube round-trip uses "Move to trash" (30-day grace). The verify step accepts a "Video unavailable" page as gone.

TikTok round-trip occasionally fails at delete with a re-auth prompt — surface to user, do not retry.

## 6. Weekly cadence

```
/weekly-plan
   # generates plan.json + plan.xlsx for current ISO week
   # includes last-week metrics review if a previous plan exists
```

Review `reports/plans/<brand>/<iso_week>/plan.xlsx`. Captions / hashtags / media paths are filled in. Tweak `plan.json` if needed (then re-run `node scripts/plan-export.mjs <plan.json>` to regenerate xlsx).

Each day:

```
/publish-from-plan --day today
   # processes today's slots in time order, sequentially
```

Or a specific slot:

```
/publish-from-plan --slot 2026-W19-ig-mon-1230
```

## 7. Triage a failed run

```
/scriptify-flow <run-id>
```

The run id appears in the final reply of every `/publish-now`, `/publish-from-plan`, and `/test-roundtrip` invocation, and in `data/runs/`.

The output shows each Playwright call (label, tool, ok / err, duration). Find the step that flipped to `err` and the surrounding context.

## 8. Multi-brand

To run multiple brands from the same repo:

```
echo other-brand > config/active-brand
# or
BRAND=other-brand /publish-now draft:<id>
```

Each brand has its own `browser_profiles/<brand>/`. First-time-login is per brand. The same skill set serves all brands; brand-specific values come from `config/brands/<slug>.yaml`.

## 9. Telegram / Line bot session

This repo does not run a bot process. To get the bot UX described in `templates/CLAUDE.user.md`:

```
cp templates/CLAUDE.user.md ~/.claude/CLAUDE.md
```

Then start Claude Code with the channel attached:

```
claude --channels plugin:telegram@claude-plugins-official
```

The session honors:

- `react` 👀 immediately on every inbound TG message.
- Plain-text replies (no markdown).
- Two-stage gate: `/draft-post` and `/weekly-plan` produce preview-only; `ok` / `go` / `yes` (or explicit slash) within 5 minutes confirms.

See `docs/OPERATING_RULES.md` for the enforced discipline.

## Common errors

| Error | Meaning | Fix |
|---|---|---|
| `profile lock conflict` | Chromium with this brand's profile is already running | `/unlock-browser` |
| `login expired, run /first-time-login` | Cookie expired on a platform | `/first-time-login` |
| `asset not found: <path>` | Draft references a file that doesn't exist | Drop the file in `media/assets/<brand>/...` or re-upload via TG |
| `url_extraction_failed` | Post likely went out, but URL couldn't be captured | Check the platform manually; the post may exist |
| `channel verification required` | YT account hasn't done the SMS verification | Verify in YT Studio, then retry |
| `tiktok challenge required` | CAPTCHA / SMS prompt mid-flow | Open TikTok manually, satisfy the prompt, retry |

## What not to do

- Don't run two `publish-*` flows in parallel — one Chromium profile per brand.
- Don't `pkill chrome` or delete `browser_profiles/<brand>/SingletonLock`. Use `/unlock-browser`.
- Don't edit `plan.xlsx` directly and expect `/publish-from-plan` to read it — `plan.json` is canonical. Edit JSON, regenerate xlsx.
- Don't share `config/brands/<slug>.yaml` with secrets in it. The schema does not include credentials by design.
