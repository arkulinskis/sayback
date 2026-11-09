"""English / Spanish for the member pages (the two sales pages are written whole in each language).

Templates keep their English and mark translatable text with data-t (attributes with data-ta="placeholder,aria-label").
After every page change router.show() calls apply(), and theme/assets/sb-i18n.js swaps each marked element to the
Spanish in window.SB_I18N (keeping the English, so switching back works). Text set from Python goes through t().
A missing Spanish entry shows the English and lands in window.SB_MISSING (the UI test fails on it).
"""
from anvil.js import window

LANGS = ("en", "es")


def lang():
    v = window.SB.lang() if window.get("SB") else "en"
    return v if v in LANGS else "en"


def set_lang(value):
    if value in LANGS and window.get("SB"):
        window.SB.setLang(value)


def t(text):
    """The Spanish for an English text when the page is in Spanish, else the English."""
    if lang() != "es" or not window.get("SB"):
        return text
    return window.SB.t(text)


def pick(pair):
    """A {"en": ..., "es": ...} dict (lesson titles, situations) in the page language."""
    if not isinstance(pair, dict):
        return pair or ""
    return pair.get(lang()) or pair.get("en") or ""


def apply(node=None):
    if window.get("SB"):
        window.SB.tr(node or window.document.body, lang())
