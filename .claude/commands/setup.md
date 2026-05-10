---
description: Interactive brand-YAML builder. Writes config/brands/<slug>.yaml + config/active-brand.
---

Walk the user through creating a brand profile. End state: a complete `config/brands/<slug>.yaml` ready for use.

## Read first

- `config/brands/_example.yaml` — schema + comments.
- Existing `config/brands/<slug>.yaml` (if any) — to decide between "new" and "edit".

## Steps

### Step 0: detect current state

List `config/brands/`:

1. If only `_example.yaml` exists and `config/active-brand` is missing or empty → ask the user for a brand slug, copy `_example.yaml` to `<slug>.yaml`, write the slug into `config/active-brand`, then continue with Step 1.
2. If `<slug>.yaml` exists but contains placeholders / empty fields → ask:
   ```
   I see a brand profile for "<display_name>". Want to:
     A. Reset (overwrite from scratch)
     B. Edit specific fields
     C. Cancel
   ```
3. If multiple brand YAMLs exist → ask which one to edit, or whether to create a new brand.

### Step 1: collect info via dialog

Ask one section at a time. For each, explain *why* you're asking and offer an example. Do not assume the user is comfortable editing YAML — keep the conversation high-level.

#### 1. Identity
- Brand slug (lowercase, hyphens; used as folder name).
- Display name.
- Primary language (`en` / `zh-TW` / `ja` / `de` / ...).
- Secondary languages (optional).

#### 2. Company
- One-paragraph description (audience + product / IP).
- Website URL.
- Contact email (optional).

#### 3. Voice
- Tone (one short phrase).
- Audience (multi).
- Emphasis (what to lean on).
- Forbidden words.
- Forbidden behavior.

#### 4. Socials (6 platforms)
For each of facebook / instagram / x / threads / youtube / tiktok, ask for the URL. Skip empty ones. Derive `handle` from the URL automatically — do not ask.

For Facebook only, also ask for `page_id` and `asset_id` (Meta Business Suite). If the user does not know, leave blank — `publish-facebook` falls back to the slower URL-extraction path.

#### 5. Storefronts
Ask: "Where can customers buy?" Free-form key/value pairs (`amazon`, `taobao`, `rakuten`, `shopify`, ...).

#### 6. Products
"List your main products one at a time. Say 'done' to finish."

For each:
- Display name.
- Category.
- 3-5 selling points.
- Target audience for this product.

Generate the `id` from the slug of the name (e.g. "Noir's Mystery Box" → `noir-mystery-box`).

#### 7. Content themes
"What themes will this brand post about? (suggest 4-6)"

Provide examples: unboxing reveal, behind-the-curation, collector spotlight, regional drop, trend / lore commentary, customer testimonial, ...

#### 8. Per-platform content style
Show defaults; ask if the user wants to override anything:

```
facebook: caption medium, 3 hashtags
instagram: caption medium, 8 hashtags, blank line then hashtag block
x: caption short, 2 hashtags
threads: caption medium, 1 hashtag
youtube: caption long, 8 tags
tiktok: caption short, 5 tags
```

### Step 2: write the YAML

Write `config/brands/<slug>.yaml` with the collected values + the standard `media_library` and `storage` paths derived from the slug. Make sure `config/active-brand` contains `<slug>`.

After writing, `cat` the file back to the user and ask: "Confirm? (yes / edit / cancel)".

### Step 3: next steps prompt

```
✅ brand profile saved: config/brands/<slug>.yaml
   active brand: <slug>

Next:
  1. Drop assets into media/assets/<slug>/
  2. Run /first-time-login to log into the 6 platforms (sessions persist in browser_profiles/<slug>/)
  3. Try /draft-post fb,ig,x,threads to make a preview
```

## Don'ts

- Do not edit `media/`, `browser_profiles/`, or `.claude/` from this command.
- Do not run `/first-time-login` automatically — let the user kick it off.
- Do not invent values to "fill in" empty fields — leave blank.
- Do not assume the user knows YAML — keep the conversation prose-driven.
