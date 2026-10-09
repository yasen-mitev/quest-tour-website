# Quest City Tour marketing site — design proposal (2026-10-09)

Static site for github.com/yasen-mitev/quest-tour-website ("repository one" of the Leaders are Builders task:
public, static, fast, SEO-ready, explains the product to someone who has never heard of it). Open `index.html`
in a browser; the pages work offline.

## Same design as the app, nothing moved

- Tokens are copied 1:1 from the app's `frontend/src/styles/quest-screens.css` (direction 02c "Evening Domes · Cards"):
  deep patina bands (`--accent-strong`) with a 2 px gold rule, light sage surface, raised white cards, sunken flat
  controls, solid gold chips, theatre-red only inside the artwork. Fonts are the app's self-hosted Onest + JetBrains Mono
  (`assets/fonts/`, copied from `frontend/src/fonts/`). The quest-tour repo is untouched.
- The skyline, the confetti, the curtain art and the filled icon glyphs are the app's own SVGs (`art.tsx`, `Icon.tsx`),
  inlined as `<symbol>`s so they recolour from the tokens.
- The product is shown as **real app frames**: 390 × 844 screens built with the app's class names and scaled with
  `--s`, not screenshots. They stay sharp at any size and change with the tokens. Screens used: Task (riddle 3 of 8,
  hero), Cover, Correct, Finish with leaderboard, and the album cover sheet (A4). Content is the Sofia sample game from
  `specs/frontend-design-brief.md` §6.
- Two type steps are added for desktop (`.t-hero` 68 px, `.t-display-xl` 44 px, both fluid); everything else is the
  app's scale. Buttons, chips, eyebrows and cards are the app's components under the same names (`btn`, `tag`, `eyebrow`, `card`).

## Page structure (home)

1. Sticky patina nav with the dome mark, five anchors, gold "Create a quest".
2. Hero band: kicker, "Turn a city walk into a quest.", lead, gold + ghost buttons, three proof points, the Task screen
   standing on the gold rule, skyline behind.
3. Overview video (`video/overview.html` storyboard rendered by `video/render.py` into `assets/overview.mp4|webm` + poster; 1280 x 720, 30 s, silent, no mail or other configurable value baked in, frame-exact from the same app frames). Rebuild after any token or copy change.
4. How it plays: the four player moves as a numbered sequence (it is a real sequence), then the penalty note with gold chips
   (+10 / +15 / +30 from R-5, R-6). The compass (R-26) is deliberately not mentioned anywhere until it is fixed (user decision 2026-10-09).
4. Three app frames: Cover, Correct, Finish.
5. For hosts (sunken band): six feature cards drawn from the requirements (private links, multi-phone sync, server clock,
   priced hints, translations, leaderboard).
6. The album: copy + A4 cover sheet (issue #33 / PR #34).
7. Setting up: three host steps.
8. Who it is for: one tinted card stating that the quests are run for friends and colleagues visiting Sofia (no pricing, decided 2026-10-09).
9. FAQ: six `<details>` (no JS needed).
10. Closing curtain band ("Coming to Sofia? Ask for a link.") with a Get in touch button, footer with Product / Hosts / Legal columns and the site version in mono.

`privacy.html` and `terms.html` show the reading layout for the legal pages the task requires (the headings a GDPR
policy needs; the text is a template the operator has to write and read).

Content column: 1400 px with a 16 to 64 px fluid gutter (widened from 1120 px on 2026-10-09; the user did not want a narrow centred page). The FAQ runs in two columns on desktop.

## Logo

Mark **B · Pin** from `design/logos.html` (chosen 2026-10-09): a map pin holding a church cupola on a drum. One `<symbol id="mark">`
in every page and in the video storyboard, with two colour roles: `--m1` pin, `--m2` cupola. On the patina bands it is a gold pin with
a patina cupola; `favicon.svg` is a patina pin with a gold cupola (gold pin on dark tabs via `prefers-color-scheme`);
`apple-touch-icon.png` is rendered from `design/apple-touch-icon.svg`. The other marks stay in `design/logos.html` for reference.

## Placeholders to decide before launch

- **Domain and contact address.** "Get in touch" points at the contact block of the privacy page; put the real address there.
- **Claim to verify:** "most teams finish in under 3 hours".
- **Compass:** hidden on the site until the heading bug is fixed; add it back to "Walk there", the penalty chips and the hosts card.
- **Features not yet upstream:** the riddle rating (stars after Correct, a word for the host at the finish, admin Feedback page) is on the fork branch `feat/riddle-rating` (issue #38) and is shown on the site and in the video on the user's request (2026-10-09).
- **SEO/launch:** OG image, `sitemap.xml`, `robots.txt`, Search Console verification, cookie notice if analytics are added.

## Proposed repo layout for quest-tour-website

```
index.html  privacy.html  terms.html  (later: how-it-works.html, for-hosts.html if the home grows)
assets/site.css  assets/fonts.css  assets/fonts/*.woff2  assets/og.png
design/README.md (this file)
.github/workflows/deploy.yml   # build-less: lint HTML, then deploy to Cloudflare Pages (task's recommended stack) or GitHub Pages
```

No framework and no build step: the site is three HTML files and one stylesheet, which keeps it fast and makes the design
reviewable in a browser tab.
