from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = set()
        self.links = set()
        self.in_main = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self.in_main = True
        if self.in_main and tag == "section" and attrs.get("id"):
            self.targets.add(attrs["id"])
        href = attrs.get("href", "")
        if href.startswith("#"):
            self.links.add(href[1:])

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False


class AnchorScrollOffsetTests(unittest.TestCase):
    def test_main_anchor_targets_clear_the_sticky_navigation(self):
        parser = AnchorParser()
        parser.feed((ROOT / "src/index.html").read_text(encoding="utf-8"))
        css = (ROOT / "assets/site.css").read_text(encoding="utf-8")

        self.assertTrue(parser.links.intersection(parser.targets), "page links should target main sections")
        self.assertRegex(
            css,
            re.compile(r"main\s*>\s*section\[id\]\s*\{[^}]*scroll-margin-top\s*:\s*(?:8\d|9\d|[1-9]\d\d)px", re.S),
            "anchor targets need at least 80px of clearance for the sticky navigation",
        )


if __name__ == "__main__":
    unittest.main()
