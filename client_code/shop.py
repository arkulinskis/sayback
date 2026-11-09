"""Buying, from any page: the landing pages' plan buttons, the Buy page, a locked lesson.

buy(product): visitors sign up first and come back to #buy/<course>; members go straight to Stripe's checkout
(a Payment Link set in Admin -> Shop), or, while no link is set yet, get the waitlist dialog.
"""
from anvil import alert
import anvil.server
from anvil.js import window

from . import i18n, router, state

COURSE_OF = {"es1": "en-es", "esall": "en-es", "esup": "en-es", "en1": "es-en", "enall": "es-en", "enup": "es-en"}


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


def buy(product):
    course = COURSE_OF.get(product, "en-es")
    if not state.me():
        router.remember_after(router.href("buy", course, product))
        state.toast(i18n.t("Make your free account first. It takes a few seconds."))
        router.go("auth", "signup")
        return
    r = state.call("checkout", product)
    if not r:
        return
    if r.get("waitlist"):
        waitlist(course)
        return
    state.store_set("sayback.pending", product)
    window.location.href = r["url"]
