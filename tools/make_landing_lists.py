"""Write Level 1's 30 lessons into both sales pages (between the lessons:start / lessons:end comments).

    python tools/make_landing_lists.py        (after tools/make_catalog.py)
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server_code"))
import lessons_data  # noqa: E402

PAGES = [("Landing", "en-es", "en"), ("LandingEs", "es-en", "es")]


def main():
    for page, course, lang in PAGES:
        f = ROOT / "client_code" / "Pages" / page / "form_template.html"
        s = f.read_text(encoding="utf-8")
        items = [ls for ls in lessons_data.DATA["courses"][course]["lessons"] if ls["level"] == 1]
        rows = "".join('\n            <li><b>%s</b><span>%s</span></li>' % (
            html.escape(ls["title"][lang]), html.escape(ls["situation"].get(lang, ""))) for ls in items)
        block = '<ol class="sb-lessons">%s\n          </ol>' % rows
        s2 = re.sub(r'(<!-- lessons:start[^>]*-->\s*)<ol class="sb-lessons">.*?</ol>', lambda m: m.group(1) + block, s, flags=re.S)
        f.write_bytes(s2.encode("utf-8"))
        print(page, len(items), "lessons")


if __name__ == "__main__":
    main()
