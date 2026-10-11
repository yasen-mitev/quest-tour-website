# Quest City Tour — marketing site

The public, static site for [quest-tour](https://github.com/yasen-mitev/quest-tour): what the game is, how it plays,
what hosts get, the surprise album, and the legal pages. No framework, no build tool beyond one Python script.

## Layout

```
site.config.json   everything site-specific: name, URL, city, host, mail addresses, app URL, legal dates
src/*.html         page templates ({{section.key}} placeholders)
build.py           renders src/*.html into the root; fails on an unknown placeholder
scripts/dev.sh     builds, serves the root on localhost, prints the URLs to check, opens the home page
index.html, privacy.html, terms.html   rendered pages (committed, so the repo serves as-is)
assets/site.css    tokens and components, copied from the app's design system (02c Evening Domes · Cards)
assets/fonts/      Onest + JetBrains Mono, self-hosted (SIL OFL)
assets/overview.*  the 30 s overview video (mp4, webm, poster)
video/             the video storyboard (overview.html, scrub it in a browser) and render.py
design/            design notes, logo proposals, touch-icon source
```

## Editing

1. Change `site.config.json` or a template in `src/`.
2. `python3 build.py` (Python 3, no dependencies).
3. Open `index.html` in a browser.

Or do all of it in one step: `./scripts/dev.sh` builds the pages, serves the repository root on
`http://localhost:8000` (or a port you pass), opens the home page, and prints the URLs for all three pages.
Ctrl-C stops the server.

CI runs the same build and fails if the committed pages are out of date.

## The video

`python3 video/render.py` screenshots `video/overview.html` frame by frame with Playwright's Chromium and encodes with
ffmpeg (`pip install playwright && playwright install chromium`, `brew install ffmpeg`). Re-render after any change to
the tokens or the captions. Nothing configurable is baked into it.

## Deploy

`.github/workflows/pages.yml` publishes the repository root to GitHub Pages on every push to `main`. Switching to
Cloudflare Pages is a one-line change: point it at the repo root with no build command.
