# AGENTS.md — guidance for AI coding agents

Quest City Tour marketing site: a static, framework-free site for the [quest-tour](https://github.com/yasen-mitev/quest-tour)
app — what the game is, how it plays, what hosts get, the surprise album, and the legal pages. No
build tool beyond one Python script; the rendered pages are committed, so the repo root serves as-is
on GitHub Pages.

## Repository layout

```
site.config.json             Everything site-specific: name, URL, city, host, mail addresses, app URL, legal dates.
                             The single source of content for the pages — edit here, not in the rendered pages.
src/*.html                   Page templates (index, privacy, terms) with {{section.key}} placeholders.
build.py                     Renders src/*.html into the site root; HTML-escapes values; fails on an
                             unknown placeholder. Also writes design/artifact.html for design review.
index.html, privacy.html,
terms.html                   Rendered pages (committed, so the repo serves as-is; never hand-edit them).
assets/site.css              Tokens and components, copied from the app's design system (02c Evening Domes · Cards).
assets/fonts/                Onest + JetBrains Mono, self-hosted (SIL OFL) — never add a third-party font host.
assets/overview.*            The 30 s overview video (mp4, webm, poster).
video/                       The video storyboard (overview.html, scrub it in a browser) and render.py.
design/                      Design notes, logo proposals, touch-icon source.
scripts/dev.sh               Builds, serves the repo root on localhost, prints the URLs to check.
.github/workflows/pages.yml  CI: rebuild and diff-check the committed pages; deploy to GitHub Pages on main.
```

## Commands

```bash
python3 build.py         # render src/*.html → root pages; fails on an unknown placeholder
./scripts/dev.sh         # build + serve on :8000 (or a port you pass) + print the URLs to check
python3 video/render.py  # re-render the overview video (needs playwright + ffmpeg, see README)
```

There is no test suite; `build.py` + the CI diff are the verification. `python3 build.py && git diff
--exit-code` must come back clean before any change is considered done — CI runs exactly this and
fails if the committed pages are out of date.

## Non-negotiable invariants (violating these is a bug even if CI passes)

- **`site.config.json` is the source of content.** Names, city, addresses, mail addresses, the app
  URL and legal dates come only from the config, rendered through `src/*.html` placeholders. Never
  hard-code site-specific text into templates, and never edit the rendered pages — the next build
  overwrites them and CI fails on the diff anyway.
- **A clean build must leave the tree unchanged.** Run `python3 build.py` and commit the regenerated
  pages in the same change as the config/template edit. CI runs `build.py`, `git diff --exit-code`
  on the pages, and a grep that no `{{` placeholder survived rendering.
- **Every value reads a CSS token.** `assets/site.css` mirrors the app's design system (02c
  "Evening Domes · Cards"); use its custom properties, never raw colours or sizes, and keep it in
  sync with the app when tokens change there.
- **Fonts stay self-hosted** from `assets/fonts/` (Onest + JetBrains Mono, SIL OFL). No third-party
  font hosts; no new external requests beyond what is already there.
- **Legal pages must match the config.** `privacy.html` / `terms.html` render `legal.*` and
  `host.*` values; if you touch a legal date, retention period, or hosting detail, change it in the
  config, not in prose.

## Gotchas

- `site.config.json` still carries intentional stand-ins (`[Host name]`, `[Hosting provider and
  region]`, `quest-tour.example`). Keep them working through the build as placeholder text; replace
  them only when real data arrives, in the config.
- `build.py` HTML-escapes every config value — config values are plain text, never markup.
- The pages link to the app at `app.url`; the app's own docs/API are out of scope here.
- The video is baked: re-render it with `video/render.py` after any change to the tokens or the
  captions, and commit the new `assets/overview.mp4` / `.webm` / poster.

## Git / PRs

- Commits and PR descriptions follow the repo's existing style (concise, imperative).
- CI expectation: the rebuild-and-diff check must pass on every PR (it runs on the root workflow,
  not per-language suites).
