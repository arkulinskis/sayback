"""Buying Sayback: prices, Stripe Payment Links, the Stripe webhook that unlocks lessons, refunds, the waitlist.

Sayback never touches card details. For each product the admin pastes a Stripe Payment Link (Admin -> Shop).
Checkout opens that link with client_reference_id = "<user id>-<product>" and the person's email filled in.
Stripe then calls <app>/_/api/stripe (event checkout.session.completed), signed with the webhook secret
(App Secret stripe_webhook_secret); the purchase row unlocks the levels. A refund in Stripe (charge.refunded)
locks them again, which is how the "Speak or it's free" guarantee is honoured.
Before any link is set, the buy buttons put people on the waitlist instead, so the page collects buyers from day one.
"""
import hashlib
import hmac
import json
import re
import time
import urllib.parse

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Catalog

PRODUCTS: dict = {
    "es1": {"course": "en-es", "kind": "level1", "levels": [1]},
    "esall": {"course": "en-es", "kind": "complete", "levels": [1, 2, 3, 4, 5]},
    "esup": {"course": "en-es", "kind": "upgrade", "levels": [2, 3, 4, 5]},
    "en1": {"course": "es-en", "kind": "level1", "levels": [1]},
    "enall": {"course": "es-en", "kind": "complete", "levels": [1, 2, 3, 4, 5]},
    "enup": {"course": "es-en", "kind": "upgrade", "levels": [2, 3, 4, 5]},
}
DEFAULTS: dict = {"currency": "$", "currency_code": "USD", "prices": {"level1": 39, "complete": 129, "upgrade": 90},
            "links": {}, "guarantee_days": 30}
TOLERANCE = 300     # seconds, as Stripe recommends
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
CONSENT = "Email me once when Sayback goes on sale. Nothing else, and I can ask to be removed any time."


def settings():
    s: dict = dict(DEFAULTS)
    saved = C.get_setting("shop") or {}
    if isinstance(saved, dict):
        s.update({k: v for k, v in saved.items() if k in DEFAULTS})
    prices: dict = dict(DEFAULTS["prices"])
    got = s.get("prices")
    if isinstance(got, dict):
        prices.update(got)
    links = s.get("links")
    s["prices"] = prices
    s["links"] = dict(links) if isinstance(links, dict) else {}
    return s


def products_for(course, user=None):
    """The offers for one course, as the Buy page and the library show them."""
    s = settings()
    owned = Catalog.owned_levels(user, course) if user is not None else set()
    out = []
    for code, p in PRODUCTS.items():
        if p["course"] != course:
            continue
        have = set(p["levels"]) <= owned
        everything = {1, 2, 3, 4, 5} <= owned
        # nothing yet: Level 1 + complete · Level 1 owners: Level 1 (owned) + the upgrade · everything: complete (owned)
        wanted = {"complete"} if everything else ({"level1", "upgrade"} if 1 in owned else {"level1", "complete"})
        if p["kind"] not in wanted:
            continue
        out.append({"product": code, "kind": p["kind"], "price": s["prices"].get(p["kind"]), "owned": have,
                    "open": bool(s["links"].get(code))})
    return out


def shop_public(course, user=None):
    s = settings()
    return {"course": course, "name": Catalog.course_name(course), "currency": s["currency"],
            "currency_code": s["currency_code"], "guarantee_days": s["guarantee_days"],
            "products": products_for(course, user), "owned": sorted(Catalog.owned_levels(user, course)),
            "signed_in": user is not None}


@anvil.server.callable
def shop_info(course):
    if not Catalog.course_ok(course):
        return C.fail("There's no such course.")
    return C.ok(**shop_public(course, C.me()))


def user_ref(user):
    """A row id like [123,4567] -> '123_4567' (Stripe's client_reference_id allows letters, digits, - and _)."""
    return re.sub(r"[^0-9]+", "_", user.get_id()).strip("_")


def user_from_ref(ref):
    m = re.fullmatch(r"(\d+)_(\d+)", ref or "")
    return C.row_by_id(app_tables.users, "[%s,%s]" % m.groups()) if m else None


@anvil.server.callable(require_user=True)
def checkout(product):
    """The Stripe address for one product, or {waitlist: True} while the shop isn't open yet."""
    me = C.require_user()
    p = PRODUCTS.get(product)
    if p is None:
        return C.fail("That isn't something we sell.")
    if set(p["levels"]) <= Catalog.owned_levels(me, p["course"]):
        return C.fail("You already own this. It's in your library.")
    link = settings()["links"].get(product) or ""
    if not link.startswith("https://"):
        return C.ok(waitlist=True, course=p["course"])
    sep = "&" if "?" in link else "?"
    url = "%s%sclient_reference_id=%s-%s&prefilled_email=%s" % (
        link, sep, user_ref(me), product, urllib.parse.quote(me["email"] or "", safe=""))
    return C.ok(url=url)


# ------------------------------------------------------------------------------------------------ purchases
def grant(user, email, product, source, amount=None, currency="", session="", intent="", note=""):
    p = PRODUCTS[product]
    return app_tables.purchases.add_row(
        user=user, email=(email or (user["email"] if user else "") or "").lower(), product=product, course=p["course"],
        levels=list(p["levels"]), amount=amount, currency=(currency or "").upper(), source=source, session=session or None,
        payment_intent=intent or None, note=note or None, refunded=False, created=C.now(), is_demo=False)


def claim_for(user):
    """Purchases made for an email before that person had an account (an admin gift) join the account."""
    email = (user["email"] or "").lower()
    if not email:
        return 0
    n = 0
    for p in app_tables.purchases.search(user=None, email=email):
        p["user"] = user
        n += 1
    return n


def purchase_dict(p, with_email=False):
    d = {"id": p.get_id(), "product": p["product"], "course": p["course"], "course_name": Catalog.course_name(p["course"]),
         "kind": PRODUCTS.get(p["product"], {}).get("kind", ""), "levels": list(p["levels"] or []),
         "amount": p["amount"], "currency": p["currency"] or "", "source": p["source"], "refunded": bool(p["refunded"]),
         "created": C.iso(p["created"]), "note": p["note"] or "", "demo": bool(p["is_demo"])}
    if with_email:
        d["email"] = p["email"] or ""
        d["name"] = C.name_of(p["user"]) if p["user"] is not None else ""
    return d


@anvil.server.callable(require_user=True)
def my_purchases():
    me = C.require_user()
    rows = sorted(app_tables.purchases.search(user=me), key=lambda r: r["created"], reverse=True)
    return {"purchases": [purchase_dict(p) for p in rows]}


@anvil.server.callable(require_user=True)
def has_product(product):
    """Polled by the thank-you page until Stripe's webhook has unlocked the purchase."""
    me = C.require_user()
    p = PRODUCTS.get(product)
    if p is None:
        return {"owned": False}
    return {"owned": set(p["levels"]) <= Catalog.owned_levels(me, p["course"]), "course": p["course"]}


# ------------------------------------------------------------------------------------------------ Stripe webhook
def _body():
    b = anvil.server.request.body
    if b is None:
        return b""
    if hasattr(b, "get_bytes"):
        return getattr(b, "get_bytes")()
    return b.encode("utf-8") if isinstance(b, str) else bytes(b)


def verify(raw, header, secret, now=None):
    """Stripe-Signature: t=<time>,v1=<hex>. True if a v1 matches HMAC-SHA256(secret, "<t>.<body>") and t is recent."""
    if not header or not secret:
        return False
    parts: dict = {}
    for kv in str(header).split(","):
        k, _, v = kv.strip().partition("=")
        parts.setdefault(k, []).append(v)
    try:
        t = int((parts.get("t") or ["0"])[0])
    except ValueError:
        return False
    if abs((now or time.time()) - t) > TOLERANCE:
        return False
    expected = hmac.new(secret.encode("utf-8"), str(t).encode("utf-8") + b"." + raw, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, v) for v in parts.get("v1", []))


def _reply(status, data):
    return anvil.server.HttpResponse(status, json.dumps(data), headers={"Content-Type": "application/json"})


def webhook_secret():
    try:
        import anvil.secrets
        return anvil.secrets.get_secret("stripe_webhook_secret") or ""
    except Exception:
        return ""


def handle_event(event):
    """Apply one verified Stripe event. Returns a short word for the reply (and the tests)."""
    kind = event.get("type")
    obj = (event.get("data") or {}).get("object") or {}
    if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        if obj.get("payment_status") not in ("paid", "no_payment_required"):
            return "waiting"   # bank transfers etc.: async_payment_succeeded comes later
        session = C.text(obj.get("id"), 120)
        if not session:
            return "no session"
        if app_tables.purchases.get(session=session) is not None:
            return "duplicate"
        ref = C.text(obj.get("client_reference_id"), 120)
        uref, _, product = ref.rpartition("-")
        if product not in PRODUCTS:
            return "unknown product"
        email = C.text(((obj.get("customer_details") or {}).get("email")) or obj.get("customer_email"), 200)
        user = user_from_ref(uref) or (app_tables.users.get(email=email.lower()) if email else None)
        amount = obj.get("amount_total") if isinstance(obj.get("amount_total"), int) else None
        grant(user, email, product, "stripe", amount=amount, currency=C.text(obj.get("currency"), 8), session=session,
              intent=C.text(obj.get("payment_intent"), 120))
        return "granted"
    if kind == "charge.refunded":
        intent = C.text(obj.get("payment_intent"), 120)
        if not intent or not obj.get("refunded"):
            return "partial refund ignored"
        n = 0
        for p in app_tables.purchases.search(payment_intent=intent):
            p["refunded"] = True
            n += 1
        return "refunded %d" % n
    return "ignored"


@anvil.server.http_endpoint("/stripe", methods=["POST"])
def stripe_webhook(**kw):
    raw = _body()
    headers = {str(k).lower(): v for k, v in (anvil.server.request.headers or {}).items()}
    secret = webhook_secret()
    if not secret:
        return _reply(503, {"error": "stripe_webhook_secret isn't set in App Secrets"})
    if not verify(raw, headers.get("stripe-signature"), secret):
        return _reply(400, {"error": "bad signature"})
    try:
        event = json.loads(raw.decode("utf-8"))
    except ValueError:
        return _reply(400, {"error": "bad json"})
    return _reply(200, {"received": True, "result": handle_event(event)})


# ------------------------------------------------------------------------------------------------ waitlist
@anvil.server.callable
def join_waitlist(email, course, source=""):
    me = C.me()
    email = C.text(email or (me["email"] if me else ""), 200).lower()
    if not EMAIL.match(email):
        return C.fail("That email doesn't look right. Check it and try again.")
    if not Catalog.course_ok(course):
        return C.fail("There's no such course.")
    if C.rate_limited("waitlist", 5, 3600):
        return C.fail("That's a lot of sign-ups from one browser. Please try again later.")
    row = app_tables.waitlist.get(email=email, course=course)
    if row is None:
        app_tables.waitlist.add_row(email=email, course=course, user=me, source=C.text(source, 120) or None,
                                    consent=CONSENT, created=C.now(), is_demo=False)
    return C.ok(already=row is not None)


# ------------------------------------------------------------------------------------------------ admin
def _secrets_status():
    from . import Audio
    return {"stripe_webhook_secret": bool(webhook_secret()), "audio": Audio.status()}


@anvil.server.callable(require_user=True)
def admin_shop():
    C.require_admin()
    origin = anvil.server.get_app_origin() or ""
    api = origin.rstrip("/") + "/_/api"
    s = settings()
    return {"settings": s, "products": [{"product": k, "course": v["course"], "course_name": Catalog.course_name(v["course"]),
                                         "kind": v["kind"], "link": s["links"].get(k, ""),
                                         "success_url": "%s/#thanks/%s" % (origin.rstrip("/"), k)}
                                        for k, v in PRODUCTS.items()],
            "webhook_url": api + "/stripe", "status": _secrets_status(), "audio_base": C.get_setting("audio_base") or "",
            "free_lessons": Catalog.free_count()}


@anvil.server.callable(require_user=True)
def admin_save_shop(data):
    C.require_admin()
    data = data if isinstance(data, dict) else {}
    s = settings()
    prices = data.get("prices") or {}
    for k in DEFAULTS["prices"]:
        try:
            v = float(prices.get(k, s["prices"][k]))
        except (TypeError, ValueError):
            return C.fail("Prices must be numbers.")
        if not 0 < v < 10000:
            return C.fail("Prices must be between 1 and 9,999.")
        s["prices"][k] = int(v) if v == int(v) else round(v, 2)
    links = data.get("links") or {}
    for k in PRODUCTS:
        link = C.text(links.get(k, s["links"].get(k, "")), 300)
        if link and not re.match(r"^https://(buy\.stripe\.com|checkout\.stripe\.com|[a-z0-9.-]+)/", link):
            return C.fail("Payment Links start with https:// (e.g. https://buy.stripe.com/...).")
        s["links"][k] = link
    s["currency"] = C.text(data.get("currency", s["currency"]), 4) or "$"
    s["currency_code"] = C.text(data.get("currency_code", s["currency_code"]), 3).upper() or "USD"
    try:
        s["guarantee_days"] = max(0, min(365, int(data.get("guarantee_days", s["guarantee_days"]))))
    except (TypeError, ValueError):
        return C.fail("The guarantee must be a number of days.")
    C.set_setting("shop", s)
    base = C.text(data.get("audio_base", C.get_setting("audio_base") or ""), 300)
    if base and not base.startswith(("http://", "https://")):
        return C.fail("The test audio address must start with https://")
    C.set_setting("audio_base", base)
    try:
        free = int(data.get("free_lessons", Catalog.free_count()))
    except (TypeError, ValueError):
        free = 1
    C.set_setting("free_lessons", max(0, min(5, free)))
    return C.ok(**admin_shop())


@anvil.server.callable(require_user=True)
def admin_sales():
    C.require_admin()
    rows = sorted(app_tables.purchases.search(), key=lambda r: r["created"], reverse=True)
    paid = [p for p in rows if not p["refunded"] and p["source"] == "stripe"]
    by_cur: dict = {}
    for p in paid:
        by_cur[p["currency"] or "?"] = by_cur.get(p["currency"] or "?", 0) + (p["amount"] or 0)
    buyers = len({(p["email"] or "") for p in rows if not p["refunded"]})
    return {"purchases": [purchase_dict(p, with_email=True) for p in rows[:300]], "total": len(rows),
            "revenue": [{"currency": k, "cents": v} for k, v in sorted(by_cur.items())], "buyers": buyers,
            "refunded": len([p for p in rows if p["refunded"]])}


@anvil.server.callable(require_user=True)
def admin_grant(email, product, note=""):
    C.require_admin()
    email = C.text(email, 200).lower()
    if not EMAIL.match(email):
        return C.fail("Type the person's email address.")
    if product not in PRODUCTS:
        return C.fail("Pick what to give them.")
    user = app_tables.users.get(email=email)
    grant(user, email, product, "admin", note=C.text(note, 200) or "Given by an admin")
    return C.ok(has_account=user is not None)


@anvil.server.callable(require_user=True)
def admin_set_refunded(purchase_id, flag):
    C.require_admin()
    p = C.row_by_id(app_tables.purchases, purchase_id)
    if p is None:
        return C.fail("That purchase no longer exists.")
    p["refunded"] = bool(flag)
    return C.ok(purchase=purchase_dict(p, with_email=True))


@anvil.server.callable(require_user=True)
def admin_waitlist():
    C.require_admin()
    rows = sorted(app_tables.waitlist.search(), key=lambda r: r["created"], reverse=True)
    items = [{"id": r.get_id(), "email": r["email"], "course": r["course"], "course_name": Catalog.course_name(r["course"]),
              "source": r["source"] or "", "created": C.iso(r["created"]), "demo": bool(r["is_demo"])} for r in rows]
    csv = "email,course,source,joined\n" + "".join(
        '"%s",%s,"%s",%s\n' % (str(i["email"]).replace('"', ""), i["course"], str(i["source"]).replace('"', ""), str(i["created"])[:10])
        for i in items if not i["demo"])
    return {"items": items[:500], "total": len(items), "csv": csv}


@anvil.server.callable(require_user=True)
def admin_waitlist_remove(entry_id):
    C.require_admin()
    r = C.row_by_id(app_tables.waitlist, entry_id)
    if r is not None:
        r.delete()
    return C.ok()


@anvil.server.callable(require_user=True)
def admin_audio_test(course="en-es"):
    """A playable link to lesson 1, so the admin can check the storage setup."""
    C.require_admin()
    from . import Audio
    ls = Catalog.lesson(course if Catalog.course_ok(course) else "en-es", "L1-01")
    url = Audio.url_for(ls["file"]) if ls else None
    return C.ok(url=url, status=Audio.status())


def overview():
    rows = list(app_tables.purchases.search())
    live = [p for p in rows if not p["refunded"]]
    cents = sum((p["amount"] or 0) for p in live if p["source"] == "stripe")
    return {"buyers": len({p["email"] for p in live}), "sales": len([p for p in live if p["source"] == "stripe"]),
            "revenue_cents": cents, "waitlist": len(app_tables.waitlist.search()),
            "currency": settings()["currency"], "shop_open": any(settings()["links"].values())}
