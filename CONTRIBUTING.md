# Contributing to Quest City Tour (marketing site)

Thanks for helping build the Quest City Tour marketing site. This guide explains how to work in this
repo: where content lives, how to build and preview the site, and what to check before opening a
pull request.

## How the site works

There is no framework and no build tool beyond one Python script. Content lives in
`site.config.json`; `src/*.html` are templates with `{{section.key}}` placeholders; `python3
build.py` renders them into the repo root (`index.html`, `privacy.html`, `terms.html`). The rendered
pages are committed, so the repository root serves as-is — GitHub Pages publishes it directly.

If code and config disagree, the config wins: site-specific text comes from `site.config.json`, not
from templates or rendered pages. Never hand-edit the rendered pages — the next build overwrites
them.

## Getting set up

Prerequisite: Python 3 only (no dependencies).

```bash
./scripts/dev.sh                 # builds, serves on http://localhost:8000, prints the URLs to check
```

Or step by step:

```bash
python3 build.py                 # render src/*.html into the repo root
python3 -m http.server 8000      # serve the repo root, then open http://localhost:8000
```

## How to verify your changes

Before opening a PR, from the repo root:

```bash
python3 build.py                 # must succeed — unknown placeholders fail the build
git diff --exit-code             # the committed pages must already be regenerated
```

CI runs exactly these checks (plus a grep that no `{{` placeholder survived rendering) and fails if
the committed pages are out of date. Then open the site locally and read the pages you changed —
there is no test suite, so eyes on the content are part of the checklist:

- the home page, the privacy page, and the terms page
- anything driven by `site.config.json` (names, city, mail addresses, app URL, legal dates)

### Video changes

The overview video is baked into `assets/overview.mp4` / `.webm`. After changing the tokens or the
captions in `video/overview.html`, re-render it (`pip install playwright && playwright install
chromium`, `brew install ffmpeg`, then `python3 video/render.py`) and commit the new assets.

## Conventions

- **Edit `site.config.json` or `src/*.html`, then run `build.py`** and commit the regenerated pages
  in the same change.
- **Styling uses the tokens in `assets/site.css`**, which mirror the app's design system (02c
  "Evening Domes · Cards"). Every colour and size reads a CSS token — no raw values — and stays in
  sync with the app when tokens change there.
- **Fonts are self-hosted** (`assets/fonts/`, Onest + JetBrains Mono, SIL OFL). Do not add
  third-party font hosts or new external requests.
- **Legal pages** (`privacy.html`, `terms.html`) render `legal.*` and `host.*` config values.
  Changes to dates, retention periods or hosting details go in the config, not in prose.
- `site.config.json` intentionally carries stand-ins (`[Host name]`, `[Hosting provider and
  region]`, `quest-tour.example`) until real data arrives — leave them working through the build.

## Opening a pull request

1. Branch from `main`; keep changes focused — a config change, a template change, or an asset
   refresh, with the regenerated pages included.
2. Make sure `python3 build.py && git diff --exit-code` is clean and you have read the affected
   pages locally (e.g. via `./scripts/dev.sh`).
3. PRs target `main`. Every merge to `main` deploys to GitHub Pages, so only merge what is ready to
   be public.

## Where to ask questions

This repo documents the [quest-tour](https://github.com/yasen-mitev/quest-tour) app; questions about
the app itself belong there. For the site, open an issue or discuss in the PR before implementing —
especially for content that ends up on the legal pages.
