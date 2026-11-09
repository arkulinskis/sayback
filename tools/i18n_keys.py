"""List every English text the member pages translate, and which ones have no Spanish yet.

    python tools/i18n_keys.py          -> prints missing keys (exit 1 if any)

Sources: data-t elements and data-ta attributes in client_code templates, i18n.t("...") calls in client Python,
and the server messages in EXTRA (errors a member can see). The Spanish lives in theme/assets/sb-i18n.js.
"""
import html.parser
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"Pages/Landing", "Pages/LandingEs", "Pages/Admin", "Items/SaleRow", "Items/WaitRow"}
EXTRA = [
    "This lesson is locked.", "You already own this. It's in your library.", "That isn't something we sell.",
    "That email doesn't look right. Check it and try again.", "There's no such course.",
    "That's a lot of sign-ups from one browser. Please try again later.", "That lesson doesn't exist.",
    "Please use at least 2 characters for your name.", "That didn't work.",
    "An account with that email already exists. Try signing in.", "Please confirm your email first. Check your inbox for the link.",
    "This account is disabled.", "Too many wrong attempts. Wait a while, or reset your password.",
    "That email and password don't match.", "Please choose a stronger password.",
    "Account created. Check your email for a confirmation link, then sign in.",
    "If that email has an account, a reset link is on its way.", "Google sign-in was cancelled.",
    "Please enter a valid email address.", "Please choose a password of at least 8 characters.", "Please enter your password.",
    "Please tell us your name.",
]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


class Grab(html.parser.HTMLParser):
    """Inner HTML of every element with data-t (as the browser would serialise simple markup)."""

    def __init__(self, raw):
        super().__init__(convert_charrefs=False)
        self.raw, self.keys, self.stack = raw, [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-ta" in a:
            for name in a["data-ta"].split(","):
                if a.get(name.strip()):
                    self.keys.append(a[name.strip()])
        if tag in ("img", "br", "input", "meta", "link", "hr"):
            return
        self.stack.append((tag, "data-t" in a, self.getpos(), self.get_starttag_text()))

    def handle_endtag(self, tag):
        while self.stack:
            t, marked, pos, start = self.stack.pop()
            if t == tag:
                if marked:
                    self.keys.append(("pos", pos, start, tag))
                break


def template_keys(path):
    raw = path.read_text(encoding="utf-8")
    raw = raw.split("\n---\n", 1)[1] if raw.startswith("---") else raw
    out = []
    for m in re.finditer(r"<(\w+)((?:\s[^>]*?)?\sdata-t(?:\s[^>]*)?)>", raw):
        tag, start = m.group(1), m.end()
        depth, i = 1, start
        pat = re.compile(r"<(/?)%s\b[^>]*>" % tag)
        while depth:
            n = pat.search(raw, i)
            if not n:
                break
            depth += -1 if n.group(1) else 1
            i = n.end()
        inner = raw[start:n.start()] if n else ""
        out.append(norm(inner))
    for m in re.finditer(r'data-ta="([^"]+)"', raw):
        tagtext = raw[raw.rfind("<", 0, m.start()):raw.find(">", m.start())]
        for name in m.group(1).split(","):
            v = re.search(r'\s%s="([^"]*)"' % re.escape(name.strip()), tagtext)
            if v:
                out.append(norm(v.group(1)))
    return out


def python_keys(path):
    text = path.read_text(encoding="utf-8")
    keys = re.findall(r'i18n\.t\("((?:[^"\\]|\\.)*)"\)', text)
    if "PLAYER_LABELS" in text:
        keys += re.findall(r'"([^"]+)"', text.split("PLAYER_LABELS = [", 1)[1].split("]", 1)[0])
    for name in ("TITLES", "BUTTONS", "KINDS"):
        m = re.search(name + r" = \{(.*?)\}", text, re.S)
        if m and "i18n" in text:
            keys += re.findall(r':\s*"([^"]+)"', m.group(1))
    if "HEADINGS = {" in text:
        keys += re.findall(r'"([^"]+)"', text.split("HEADINGS = {", 1)[1].split("}", 1)[0])
        keys = [k for k in keys if k not in ("login", "signup", "reset")]
    return [norm(k.replace('\\"', '"')) for k in keys]


def all_keys():
    keys = []
    for f in sorted((ROOT / "client_code").rglob("*")):
        rel = f.relative_to(ROOT / "client_code").as_posix()
        if any(rel.startswith(s) for s in SKIP):
            continue
        if f.name == "form_template.html":
            keys += template_keys(f)
        elif f.suffix == ".py":
            keys += python_keys(f)
    keys += EXTRA
    seen, out = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def pack():
    js = (ROOT / "theme" / "assets" / "sb-i18n.js").read_text(encoding="utf-8")
    body = js.split("window.SB_I18N = ", 1)[1].rsplit(";", 1)[0]
    return json.loads(body)


if __name__ == "__main__":
    keys, have = all_keys(), pack()
    missing = [k for k in keys if k not in have]
    if "--json" in sys.argv:
        print(json.dumps(missing, ensure_ascii=False, indent=1))
    else:
        for k in missing:
            print("MISSING", k)
        print("%d keys, %d missing" % (len(keys), len(missing)))
    sys.exit(1 if missing else 0)
