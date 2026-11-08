from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
VOID = {"input", "br", "img", "meta", "link", "hr", "source", "use", "path", "rect"}


class FormParser(HTMLParser):
    """Collects the request form's controls, the labels that wrap them and the page's scripts."""

    def __init__(self):
        super().__init__()
        self.form = None
        self.in_form = False
        self.stack = []
        self.controls = []   # (tag, attrs, enclosing label tag attrs or None)
        self.label_links = {}  # control name -> hrefs inside its wrapping label
        self.scripts = []
        self.ids = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids[attrs["id"]] = (tag, attrs)
        if tag == "script":
            self.scripts.append(attrs)
        if tag == "form" and attrs.get("id") == "request-form":
            self.form = attrs
            self.in_form = True
        if self.in_form and tag in ("input", "select", "textarea", "button"):
            label = next((a for t, a in reversed(self.stack) if t == "label"), None)
            self.controls.append((tag, attrs, label))
            if label is not None and attrs.get("name"):
                self.label_links.setdefault(attrs["name"], [])
        if self.in_form and tag == "a" and attrs.get("href"):
            label = next((a for t, a in reversed(self.stack) if t == "label"), None)
            if label is not None:
                for t, a, _ in reversed(self.controls):
                    if t == "input" and a.get("type") == "checkbox":
                        self.label_links.setdefault(a.get("name"), []).append(attrs["href"])
                        break
        if tag not in VOID:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag == "form" and self.in_form:
            self.in_form = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def named(self, name):
        return [c for c in self.controls if c[1].get("name") == name]


def parse(path):
    parser = FormParser()
    parser.feed((ROOT / path).read_text(encoding="utf-8"))
    return parser


class RequestFormMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = parse("src/index.html")
        cls.rendered = parse("index.html")

    def test_form_carries_the_api_origin_and_terms_version(self):
        self.assertIsNotNone(self.src.form, "src/index.html needs <form id=request-form>")
        self.assertEqual(self.src.form.get("data-api"), "{{app.url}}")
        self.assertEqual(self.src.form.get("data-terms-version"), "{{legal.updated}}")
        self.assertEqual(self.rendered.form.get("data-api"), CONFIG["app"]["url"])
        self.assertEqual(self.rendered.form.get("data-terms-version"), CONFIG["legal"]["updated"])

    def test_every_field_is_labelled(self):
        expected = {
            "game_key": "select", "play_date": "input", "team_name": "input", "team_key": "input",
            "team_participants": "input", "contact_name": "input", "contact_email": "input",
            "contact_phone": "input", "message": "textarea", "terms_accepted": "input",
        }
        for name, tag in expected.items():
            found = self.src.named(name)
            self.assertTrue(found, f"missing control {name}")
            self.assertEqual(found[0][0], tag, name)
            self.assertIsNotNone(found[0][2], f"{name} must sit inside a <label>")

    def test_required_and_input_types(self):
        for name in ("game_key", "play_date", "team_name", "team_key", "contact_name", "terms_accepted"):
            self.assertIn("required", self.src.named(name)[0][1], f"{name} is required")
        self.assertEqual(self.src.named("play_date")[0][1].get("type"), "date")
        self.assertEqual(self.src.named("contact_email")[0][1].get("type"), "email")
        self.assertEqual(self.src.named("contact_phone")[0][1].get("type"), "tel")
        self.assertEqual(self.src.named("terms_accepted")[0][1].get("type"), "checkbox")
        self.assertEqual(self.src.named("team_participants")[0][1].get("type"), "number")

    def test_honeypot_is_hidden_from_people_and_assistive_tech(self):
        tag, attrs, label = self.src.named("website")[0]
        self.assertEqual(attrs.get("tabindex"), "-1")
        self.assertEqual(attrs.get("autocomplete"), "off")
        self.assertNotIn("required", attrs)
        self.assertEqual(label.get("aria-hidden"), "true", "the honeypot wrapper is aria-hidden")
        self.assertIn("hp", label.get("class", ""))

    def test_consent_links_to_terms_and_privacy(self):
        links = self.src.label_links.get("terms_accepted", [])
        self.assertIn("terms.html", links)
        self.assertIn("privacy.html", links)

    def test_status_area_and_no_js_fallback(self):
        tag, attrs = self.src.ids["request-status"]
        self.assertEqual(attrs.get("aria-live"), "polite")
        tag, attrs = self.src.ids["request-fallback"]
        self.assertEqual(tag, "p")
        self.assertIn("hidden", self.src.form, "the form stays hidden until the script has the games")
        self.assertIn('id="request-fallback"', (ROOT / "src/index.html").read_text(encoding="utf-8"))
        rendered = (ROOT / "index.html").read_text(encoding="utf-8")
        fallback = re.search(r'id="request-fallback".*?</p>', rendered, re.S).group(0)
        self.assertIn(f'href="{CONFIG["app"]["repo"]}"', fallback)

    def test_script_is_local_and_deferred(self):
        scripts = [s for s in self.src.scripts if s.get("src")]
        self.assertEqual([s["src"] for s in scripts], ["assets/request-form.js"])
        self.assertIn("defer", scripts[0])
        self.assertTrue((ROOT / "assets/request-form.js").is_file())

    def test_templates_contain_no_hard_coded_urls(self):
        for page in ("index", "privacy", "terms"):
            self.assertNotIn("http", (ROOT / f"src/{page}.html").read_text(encoding="utf-8"), page)

    def test_rendered_pages_have_no_unresolved_placeholders(self):
        for page in ("index.html", "privacy.html", "terms.html"):
            self.assertNotIn("{{", (ROOT / page).read_text(encoding="utf-8"), page)


class LegalPagesTests(unittest.TestCase):
    def test_config_carries_the_retention_period_and_a_fresh_date(self):
        self.assertEqual(CONFIG["legal"]["request_retention_days"], "30")
        self.assertEqual(CONFIG["legal"]["updated"], "8 November 2026")

    def test_privacy_renders_retention_and_form_data(self):
        template = (ROOT / "src/privacy.html").read_text(encoding="utf-8")
        self.assertIn("{{legal.request_retention_days}}", template)
        rendered = (ROOT / "privacy.html").read_text(encoding="utf-8")
        self.assertIn(f'{CONFIG["legal"]["request_retention_days"]} days after', rendered)
        self.assertIn("pending", rendered.lower())
        self.assertIn("photos", rendered.lower())

    def test_terms_cover_team_data_and_photos_storage(self):
        text = (ROOT / "terms.html").read_text(encoding="utf-8").lower()
        self.assertIn("team names", text)
        self.assertIn("photos", text)
        self.assertIn("privacy.html", text)


class StyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
        start = css.index("/* Request form")
        end = css.find("\n/* ", start + 5)
        cls.block = css[start:end if end != -1 else len(css)]

    def test_form_rules_use_tokens_only(self):
        self.assertNotRegex(self.block, r"#[0-9a-fA-F]{3,8}\b")
        self.assertNotRegex(self.block, r"rgba?\(")
        self.assertIn("var(--tap-min)", self.block)
        self.assertIn(":focus-visible", self.block)

    def test_honeypot_is_moved_off_screen_not_display_none(self):
        rule = re.search(r"\.hp\s*\{([^}]*)\}", self.block)
        self.assertIsNotNone(rule, "needs a .hp rule")
        self.assertNotIn("display: none", rule.group(1))
        self.assertNotIn("visibility: hidden", rule.group(1))
        self.assertRegex(rule.group(1), r"position\s*:\s*absolute")
        self.assertRegex(rule.group(1), r"left\s*:\s*-\d+")


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "assets/request-form.js").read_text(encoding="utf-8")

    def test_no_external_urls_and_no_wall_clock(self):
        self.assertNotRegex(self.js, r"https?://")
        self.assertNotIn("Date.now", self.js)
        self.assertNotIn("new Date", self.js)
        self.assertIn("performance.now", self.js)

    def test_timing_comes_from_the_challenge_response(self):
        self.assertIn("min_fill_seconds", self.js)
        self.assertIn("expires_in_seconds", self.js)

    def test_talks_to_the_three_public_endpoints_only(self):
        found = set(re.findall(r"/api/public/[a-z/]+", self.js))
        self.assertEqual(found, {"/api/public/games", "/api/public/requests/challenge", "/api/public/requests"})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_solve_finds_the_number_and_gives_up_past_maxnumber(self):
        salt = "00112233445566778899aabbccddeeff?expires=1790000000"
        number = 1234
        challenge = hashlib.sha256(f"{salt}{number}".encode()).hexdigest()
        script = """
const { solve } = require(process.argv[1]);
const [challenge, salt] = process.argv.slice(2);
(async () => {
  const out = [
    await solve(challenge, salt, 5000),
    await solve(challenge, salt, 1234),
    await solve(challenge, salt, 1233),
    await solve(challenge, salt + 'x', 5000),
  ];
  console.log(JSON.stringify(out));
})();
"""
        done = subprocess.run(
            ["node", "-e", script, str(ROOT / "assets/request-form.js"), challenge, salt],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), [1234, 1234, None, None])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_solve_accepts_number_zero(self):
        salt = "ff?expires=1"
        challenge = hashlib.sha256(f"{salt}0".encode()).hexdigest()
        script = "require(process.argv[1]).solve(process.argv[2], process.argv[3], 10).then(n => console.log(JSON.stringify(n)))"
        done = subprocess.run(
            ["node", "-e", script, str(ROOT / "assets/request-form.js"), challenge, salt],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), 0)


if __name__ == "__main__":
    unittest.main()
