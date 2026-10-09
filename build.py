#!/usr/bin/env python3
"""Render src/*.html into the site root using site.config.json.

Placeholders are {{section.key}}; values are HTML-escaped. Unknown placeholders fail the build,
so a typo never ships as literal braces. No dependencies beyond the standard library.
Also writes design/artifact.html (index without the document skeleton) for the design review page.
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\.([a-z_]+)\s*\}\}")


def lookup(section: str, key: str) -> str:
    try:
        value = CONFIG[section][key]
    except KeyError:
        sys.exit(f"site.config.json has no value for {{{{{section}.{key}}}}}")
    return html.escape(str(value), quote=True)


def render(text: str) -> str:
    return PLACEHOLDER.sub(lambda m: lookup(m.group(1), m.group(2)), text)


def main() -> None:
    pages = sorted((ROOT / "src").glob("*.html"))
    for src in pages:
        out = render(src.read_text(encoding="utf-8"))
        (ROOT / src.name).write_text(out, encoding="utf-8")
        print(f"{src.name}: {len(out):,} bytes")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    head = re.search(r"<head>(.*?)</head>", index, re.S).group(1)
    body = re.search(r"<body>(.*)</body>", index, re.S).group(1)
    head = re.sub(r'<meta charset[^>]*>|<meta name="viewport"[^>]*>|<link rel="canonical"[^>]*>', "", head).strip()
    (ROOT / "design" / "artifact.html").write_text(head + "\n" + body, encoding="utf-8")


if __name__ == "__main__":
    main()
