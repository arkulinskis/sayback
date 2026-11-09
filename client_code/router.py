"""Page addresses: #name/arg1/arg2 -> a page Form (open_form), with sign-in rules.

Links in templates are plain <a href="#home">; code calls router.go("lesson", course, code).
In-page jumps (to a section of the same page) are <a href="#offer" data-scroll>: they scroll, they don't route.

    PAGES[name] = (who may open it, tab title in English, tab title in Spanish)
                  who: None = anyone, "guest" = signed out only, "user", "admin"
    NAV = the main menu (header + phone tab bar, signed-in people): (page, label, icon). At most 4.
New page: add it to PAGES, to _form() and (if it belongs in the menu) to NAV.
"""
import anvil
import anvil.js
from anvil.js import window

from . import i18n, state

PAGES = {
    "landing": (None, "Speak Spanish in your stolen minutes", "Habla español en tus minutos robados"),
    "es": (None, "Habla inglés en tus minutos robados", "Habla inglés en tus minutos robados"),
    "auth": ("guest", "Sign in", "Entrar"),
    "home": ("user", "Your library", "Tu biblioteca"),
    "lesson": ("user", "Lesson", "Lección"),
    "buy": (None, "Get the course", "Consigue el curso"),
    "thanks": ("user", "Thank you", "Gracias"),
    "profile": ("user", "Your account", "Tu cuenta"),
    "admin": ("admin", "Admin", "Admin"),
}
NAV = [("home", "Library", "headphones"), ("buy", "Courses", "cart")]
APP_NAME = "Sayback"
_r: dict = {"after": "", "listening": False, "page": None, "form": None}


def _form(name):
    """The page's Form class (imported when first needed, so start-up stays quick)."""
    if name == "landing":
        from .Pages.Landing import Landing
        return Landing
    if name == "es":
        from .Pages.LandingEs import LandingEs
        return LandingEs
    if name == "auth":
        from .Pages.Auth import Auth
        return Auth
    if name == "home":
        from .Pages.Library import Library
        return Library
    if name == "lesson":
        from .Pages.Lesson import Lesson
        return Lesson
    if name == "buy":
        from .Pages.Buy import Buy
        return Buy
    if name == "thanks":
        from .Pages.Thanks import Thanks
        return Thanks
    if name == "profile":
        from .Pages.Profile import Profile
        return Profile
    from .Pages.Admin import Admin
    return Admin


def parse(hash_text):
    h = (hash_text or "").lstrip("#").lstrip("!").lstrip("/").split("?")[0]
    parts = [window.decodeURIComponent(p) for p in h.split("/") if p]
    return (parts[0] if parts else ""), parts[1:]


def href(name, *args):
    """'#name/arg1/arg2' with every part URL-encoded."""
    return "#" + "/".join([name] + [window.encodeURIComponent(str(a)) for a in args if a not in (None, "")])


def home_page():
    if state.me():
        return "home"
    return "es" if i18n.lang() == "es" else "landing"


def current():
    return _r["page"]


def show():
    """Open the page for the current address."""
    name, args = parse(window.location.hash)
    if name not in PAGES:
        name, args = home_page(), []
    who = PAGES[name][0]
    if who == "guest" and state.me():
        name, args = "home", []
    elif who in ("user", "admin") and not state.me():
        _r["after"] = window.location.hash
        name, args = "auth", []
    elif who == "admin" and not state.is_admin():
        state.toast(i18n.t("That page is for admins only."), "error")
        name, args = "home", []
    if name == "es":
        i18n.set_lang("es")
    elif name == "landing":
        i18n.set_lang("en")
    old = _r["form"]
    if old is not None and hasattr(old, "leave"):
        old.leave()  # stop a page's audio and timers before the next page opens
    titles = PAGES[name]
    window.document.title = (titles[2] if i18n.lang() == "es" else titles[1]) + " · " + APP_NAME
    i18n.set_lang(i18n.lang())  # also sets <html lang>
    window.UI_READY = False
    page = _form(name)(args=args)
    _r["page"], _r["form"] = name, page
    anvil.open_form(page)
    shell = getattr(page, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(name)  # Anvil reuses the layout between pages: tell it who is signed in and which page is open
    i18n.apply()
    window.scrollTo(0, 0)
    window.UI_READY = True  # tests and screenshots wait for this


def go(name, *args):
    """Go to a page. Same address again = reload the page."""
    target = href(name, *args)
    if window.location.hash == target:
        show()
    else:
        window.location.hash = target


def replace(name, *args):
    """Change the address without opening anything (a page that switches its own view)."""
    window.history.replaceState(None, "", href(name, *args))


def after_sign_in():
    """Where to go once someone signs in: the page they were heading for, or home."""
    target = _r["after"]
    _r["after"] = ""
    if target and target != window.location.hash:
        window.location.hash = target
    else:
        go("home")


def remember_after(target):
    _r["after"] = target


def _on_hash(event):
    show()


def _on_click(event):
    """In-app links only change the hash. Anvil puts a <base href> in the page, so "#offer" would otherwise resolve
    against the bare app address and reload everything for a visitor who came in with ?utm_source=... (every ad)."""
    if event.defaultPrevented or event.button or event.ctrlKey or event.metaKey or event.shiftKey or event.altKey:
        return
    target = event.target
    link = target.closest("a[href^='#']") if target and getattr(target, "closest", None) else None
    if not link or link.getAttribute("target"):
        return
    event.preventDefault()
    where = link.getAttribute("href")
    if link.hasAttribute("data-scroll"):
        spot = window.document.getElementById(where[1:])
        if spot:
            spot.scrollIntoView({"behavior": "smooth", "block": "start"})
        return
    window.location.hash = where


def start():
    if not _r["listening"]:
        window.addEventListener("hashchange", anvil.js.report_exceptions(_on_hash))
        window.document.addEventListener("click", anvil.js.report_exceptions(_on_click))
        _r["listening"] = True
    show()
