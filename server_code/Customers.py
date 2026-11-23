"""Customers and ads: who bought what, where they came from, and which ad pages earn their keep.

Ad tracking is first-touch and cookie-free: client_code/ads.py keeps the first ad visit's utm_source / utm_medium /
utm_campaign / utm_content and the page it landed on (e.g. #learn/french) in the browser for 60 days, and sends it
once after sign-in (note_ad). It is stored on the account (users.ad_source) and never shared. Admin -> Customers
lists every account with its purchases, gifts and listening; Admin -> Ads adds them up per source/campaign/page and
builds ad links.
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import courses as K

FIELDS = ("source", "medium", "campaign", "content", "page", "ref", "first")


def _clean(ad):
    if not isinstance(ad, dict):
        return None
    out = {k: C.text(ad.get(k), 120) for k in FIELDS if ad.get(k)}
    return out or None


@anvil.server.callable(require_user=True)
def note_ad(ad):
    """Remember where this account first came from (only if nothing is stored yet)."""
    me = C.require_user()
    ad = _clean(ad)
    if not ad:
        return C.ok(saved=False)
    try:
        if me["ad_source"]:
            return C.ok(saved=False)
        me["ad_source"] = ad
    except Exception:
        return C.ok(saved=False)   # column not accepted yet (Schema Mismatch): nothing breaks
    return C.ok(saved=True)


def _ad_of(user):
    try:
        return user["ad_source"] or {}
    except Exception:
        return {}


def _minutes(user):
    return int(sum((r["seconds"] or 0) for r in app_tables.listening.search(user=user)) // 60)


@anvil.server.callable(require_user=True)
def admin_customers(query=""):
    """Every account with what it owns (newest first). query filters by email/name/course/source."""
    C.require_admin()
    q = C.text(query, 80).lower()
    buys: dict = {}
    for p in app_tables.purchases.search():
        if p["user"] is None:
            continue
        buys.setdefault(p["user"].get_id(), []).append(p)
    gifts: dict = {}
    for g in app_tables.gifts.search():
        if g["buyer"] is not None:
            gifts.setdefault(g["buyer"].get_id(), []).append(g)
    out: list = []
    for u in app_tables.users.search():
        uid = u.get_id()
        mine = [p for p in buys.get(uid, []) if not p["refunded"]]
        ad = _ad_of(u)
        courses = sorted({p["course"] for p in mine})
        spent = sum((p["amount"] or 0) for p in mine if p["source"] == "stripe")
        spent += sum((g["amount"] or 0) for g in gifts.get(uid, []) if not g["refunded"])
        row: dict = {"id": uid, "email": u["email"] or "", "name": C.name_of(u), "joined": C.iso(u["signed_up"]),
               "last_seen": C.iso(u["last_seen"]) if u["last_seen"] else "",
               "courses": [K.COURSES[c]["lang"] if c in K.COURSES else c for c in courses],
               "how": sorted({p["source"] for p in mine}), "spent_cents": spent,
               "gifts_bought": len(gifts.get(uid, [])), "minutes": _minutes(u),
               "source": ad.get("source", ""), "campaign": ad.get("campaign", ""), "page": ad.get("page", ""),
               "demo": bool(u["is_demo"])}
        hay = " ".join([row["email"], row["name"], " ".join(row["courses"]), row["source"], row["campaign"], row["page"]]).lower()
        if q and q not in hay:
            continue
        out.append(row)
    out.sort(key=lambda r: r["joined"] or "", reverse=True)
    paying = [r for r in out if r["spent_cents"] or r["how"]]
    csv = "email,name,joined,courses,how,spent,gifts_bought,minutes,source,campaign,page\n" + "".join(
        '"%s","%s",%s,"%s","%s",%.2f,%d,%d,"%s","%s","%s"\n' % (
            r["email"].replace('"', ""), r["name"].replace('"', ""), r["joined"][:10], " ".join(r["courses"]),
            " ".join(r["how"]), r["spent_cents"] / 100.0, r["gifts_bought"], r["minutes"], r["source"].replace('"', ""),
            r["campaign"].replace('"', ""), r["page"].replace('"', ""))
        for r in out if not r["demo"])
    return {"customers": out[:400], "total": len(out), "paying": len(paying), "csv": csv}


@anvil.server.callable(require_user=True)
def admin_ads():
    """Sign-ups, buyers and revenue per ad source / campaign / landing page."""
    C.require_admin()
    rows: dict = {}
    spent: dict = {}
    for p in app_tables.purchases.search():
        if p["user"] is not None and not p["refunded"] and p["source"] == "stripe":
            spent[p["user"].get_id()] = spent.get(p["user"].get_id(), 0) + (p["amount"] or 0)
    for g in app_tables.gifts.search():
        if g["buyer"] is not None and not g["refunded"] and g["source"] == "stripe":
            spent[g["buyer"].get_id()] = spent.get(g["buyer"].get_id(), 0) + (g["amount"] or 0)
    for u in app_tables.users.search():
        ad = _ad_of(u)
        key = (ad.get("source") or "(direct)", ad.get("campaign") or "", ad.get("page") or "")
        r = rows.setdefault(key, {"source": key[0], "campaign": key[1], "page": key[2], "signups": 0, "buyers": 0,
                                  "revenue_cents": 0})
        r["signups"] += 1
        cents = spent.get(u.get_id(), 0)
        if cents:
            r["buyers"] += 1
            r["revenue_cents"] += cents
    out = sorted(rows.values(), key=lambda r: (-r["revenue_cents"], -r["signups"]))
    for r in out:
        r["conversion"] = round(100.0 * r["buyers"] / r["signups"], 1) if r["signups"] else 0.0
    pages = [{"page": "#learn/" + K.COURSES[c]["slug"], "label": "%s (for English speakers)" % K.COURSES[c]["lang"]}
             for c in K.FOR_LEARNER["en"]]
    pages += [{"page": "#es", "label": "English (for Spanish speakers, page in Spanish)"},
              {"page": "#gift", "label": "Gift page (give it to Dad)"},
              {"page": "#landing", "label": "Chooser (which language?)"}]
    return {"rows": out, "pages": pages, "origin": (anvil.server.get_app_origin() or "").rstrip("/")}
