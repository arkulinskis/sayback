"""Gifts: someone buys a course for someone else (the "give it to Dad" offer).

Flow: the giver presses "Give as a gift" -> Shop.checkout(product, gift=True) -> the same Stripe Payment Link with
client_reference_id "<user>-g<product>" -> the webhook calls create() -> a gifts row with a random code. The giver
personalises it (to whom, a short message) on #gift/card/<code>, prints the card or sends the link
#redeem/<code>. The person who gets it makes a free account and redeem() unlocks the course in THEIR library
(a purchase row with source "gift" and the gift's payment_intent, so a Stripe refund locks it again).
Codes are 12 random letters/digits (no 0/O/1/I), so they can't be guessed.
"""
import secrets as pysecrets

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import courses as K

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_code():
    while True:
        code = "".join(pysecrets.choice(ALPHABET) for _ in range(12))
        if app_tables.gifts.get(code=code) is None:
            return code


def nice(code):
    """ABCD-EFGH-JKLM for the printed card."""
    c = (code or "").upper()
    return "-".join(c[i:i + 4] for i in range(0, len(c), 4))


def clean(code):
    return "".join(ch for ch in str(code or "").upper() if ch in ALPHABET)[:12]


def create(buyer, email, product, amount=None, currency="", session="", intent="", source="stripe"):
    return app_tables.gifts.add_row(
        code=new_code(), product=product, buyer=buyer, buyer_email=(email or (buyer["email"] if buyer else "") or "").lower(),
        to_name=None, message=None, amount=amount, currency=(currency or "").upper(), session=session or None,
        payment_intent=intent or None, source=source, created=C.now(), redeemed_by=None, redeemed_at=None,
        refunded=False, is_demo=False)


def _product_label(product):
    from . import Shop
    return Shop.product_name(product)


def card(g, for_buyer=False):
    p = K.PRODUCTS.get(g["product"]) or {}
    d = {"code": g["code"], "nice": nice(g["code"]), "product": g["product"], "kind": p.get("kind", ""),
         "courses": list(p.get("courses") or []), "label": _product_label(g["product"]),
         "to_name": g["to_name"] or "", "message": g["message"] or "",
         "from_name": (C.name_of(g["buyer"]).split(" ")[0] if g["buyer"] is not None else ""),
         "redeemed": g["redeemed_by"] is not None, "refunded": bool(g["refunded"])}
    if for_buyer:
        d["created"] = C.iso(g["created"])
        d["redeemed_at"] = C.iso(g["redeemed_at"]) if g["redeemed_at"] else ""
    return d


@anvil.server.callable(require_user=True)
def my_gifts():
    """The gifts I bought (newest first), for the gift page and the thank-you page."""
    me = C.require_user()
    rows = sorted(app_tables.gifts.search(buyer=me), key=lambda r: r["created"], reverse=True)
    return {"gifts": [card(g, True) for g in rows]}


@anvil.server.callable(require_user=True)
def latest_gift(product):
    """The thank-you page polls this until Stripe's webhook has made the gift."""
    me = C.require_user()
    rows = [g for g in app_tables.gifts.search(buyer=me, product=product) if g["redeemed_by"] is None]
    if not rows:
        return {"gift": None}
    g = max(rows, key=lambda r: r["created"])
    return {"gift": card(g, True) if (C.now() - g["created"]).total_seconds() < 86400 else None}


@anvil.server.callable(require_user=True)
def gift_card(code):
    me = C.require_user()
    g = app_tables.gifts.get(code=clean(code))
    if g is None or (g["buyer"] != me and not C.is_admin(me)):
        return C.fail("That gift isn't in your account.")
    return C.ok(gift=card(g, True))


@anvil.server.callable(require_user=True)
def set_gift_note(code, to_name, message):
    me = C.require_user()
    g = app_tables.gifts.get(code=clean(code))
    if g is None or g["buyer"] != me:
        return C.fail("That gift isn't in your account.")
    g.update(to_name=C.text(to_name, 60) or None, message=C.text(message, 280) or None)
    return C.ok(gift=card(g, True))


@anvil.server.callable
def gift_public(code):
    """What the redeem page shows before signing in: the course, who it's from, the message. Rate-limited."""
    if C.rate_limited("gift_look", 30, 3600):
        return C.fail("Too many tries. Please wait a little and try again.")
    g = app_tables.gifts.get(code=clean(code))
    if g is None:
        return C.fail("We can't find that gift code. Check the letters on the card.")
    return C.ok(gift=card(g))


@anvil.server.callable(require_user=True)
def redeem_gift(code):
    me = C.require_user()
    if C.rate_limited("gift_redeem", 20, 3600):
        return C.fail("Too many tries. Please wait a little and try again.")
    g = app_tables.gifts.get(code=clean(code))
    if g is None:
        return C.fail("We can't find that gift code. Check the letters on the card.")
    if g["refunded"]:
        return C.fail("This gift was refunded, so it can't be opened any more.")
    if g["redeemed_by"] is not None:
        if g["redeemed_by"] == me:
            return C.ok(course=(K.PRODUCTS[g["product"]]["courses"])[0], already=True)
        return C.fail("This gift has already been opened by someone else.")
    from . import Shop
    giver = C.name_of(g["buyer"]) if g["buyer"] is not None else "someone"
    Shop.grant(me, me["email"], g["product"], "gift", currency=g["currency"] or "", intent=g["payment_intent"] or "",
               note="Gift from %s (%s)" % (giver, nice(g["code"])))
    g.update(redeemed_by=me, redeemed_at=C.now())
    return C.ok(course=K.PRODUCTS[g["product"]]["courses"][0], already=False)


# ------------------------------------------------------------------------------------------------ admin
@anvil.server.callable(require_user=True)
def admin_gifts():
    C.require_admin()
    rows = sorted(app_tables.gifts.search(), key=lambda r: r["created"], reverse=True)
    out = []
    for g in rows[:300]:
        d = card(g, True)
        d.update(buyer_email=g["buyer_email"] or "", amount=g["amount"], currency=g["currency"] or "",
                 redeemed_email=(g["redeemed_by"]["email"] if g["redeemed_by"] is not None else ""),
                 demo=bool(g["is_demo"]))
        out.append(d)
    return {"gifts": out, "total": len(rows), "open": len([g for g in rows if g["redeemed_by"] is None and not g["refunded"]])}


@anvil.server.callable(require_user=True)
def admin_make_gift(product, note=""):
    """A free gift code (a prize, a podcast giveaway, a partner): no payment, redeemable like a bought one."""
    me = C.require_admin()
    if product not in K.PRODUCTS:
        return C.fail("Pick what the gift unlocks.")
    g = create(me, me["email"], product, source="admin")
    g["message"] = C.text(note, 280) or None
    return C.ok(gift=card(g, True))
