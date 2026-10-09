#!/usr/bin/env bash
# Local dev run for the static site: build the pages, serve the repo root,
# and print every URL worth checking. `python3 build.py` fails on an unknown
# placeholder, so the build doubles as the content-integrity check; the pages
# it writes are committed, so always run this before committing. Ctrl-C stops
# the server. Port comes from $1 or PORT (default 8000).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-${PORT:-8000}}"

command -v python3 >/dev/null || { echo "[dev] Missing on PATH: python3 (see README prerequisites)." >&2; exit 1; }

banner() { printf '[dev] %s\n' "$1"; }

cd "$ROOT"
banner "==> python3 build.py"
python3 build.py

echo
banner "==> Serving $ROOT at http://localhost:$PORT/"
banner "==> Ctrl-C stops the server."
banner ""
banner "Pages to check:"
banner "  http://localhost:$PORT/              home"
banner "  http://localhost:$PORT/privacy.html  privacy"
banner "  http://localhost:$PORT/terms.html    terms"
banner ""
banner "Content comes from site.config.json rendered by build.py — edit there, not in these pages."
banner "In a browser: Cmd/Ctrl-R hard-reloads after a rebuild."

# Open the home page last, after the summary, so the URLs stay visible in the
# terminal while the page loads. Best-effort: CI and headless machines have no GUI.
if command -v open >/dev/null 2>&1; then
  open "http://localhost:$PORT/" || true
fi

exec python3 -m http.server "$PORT"
