"""Buying, from any page: the sales pages' plan buttons, the Buy page, the gift page, a locked lesson.

buy(product, gift=False): visitors sign up first and come back to #buy/<course> (or #gift); members go straight to
Stripe's checkout (a Payment Link set in Admin -> Shop), or, while no link is set yet, get the waitlist dialog.
A gift uses the same Payment Link; the webhook turns it into a gift code (server_code/Gifts.py).
"""
from anvil import alert
import anvil.server
from anvil.js import window

from . import courses, i18n, router, state

COURSE_OF = {code: p["courses"][0] for code, p in courses.PRODUCTS.items()}


def info(course):
    """Prices and offers for a course (no spinner: pages show their own defaults until it arrives)."""
    try:
        r = anvil.server.call_s("shop_info", course)
    except Exception:
        return None
    return r if isinstance(r, dict) and r.get("ok") else None


def money(shop, amount):
    if amount is None:
        return ""
    n = int(amount) if float(amount) == int(amount) else amount
    return "%s%s" % (shop.get("currency") or "$", n)


def waitlist(course):
    from .Dialogs.Waitlist import Waitlist
    alert(Waitlist(course=course), buttons=[], role="app-dialog")


def buy(product, gift=False):
    course = COURSE_OF.get(product, "en-es")
    if not state.me():
        router.remember_after(router.href("gift", course) if gift else router.href("buy", course, product))
        state.toast(i18n.t("Make your free account first. It takes a few seconds."))
        router.go("auth", "signup")
        return
    r = state.call("checkout", product, bool(gift))
    if not r:
        return
    if r.get("waitlist"):
        waitlist(course)
        return
    state.store_set("sayback.pending", product)
    state.store_set("sayback.pending_gift", bool(gift))
    window.location.href = r["url"]
