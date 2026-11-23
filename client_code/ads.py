"""Where people came from (first touch, kept in this browser for 60 days, no cookies, no tracking scripts).

An ad links to a page with UTM tags, before or after the hash, e.g.
    https://spokenmiles.com/?utm_source=meta&utm_campaign=dad-gift#gift
    https://spokenmiles.com/#learn/french?utm_source=google&utm_campaign=french-commute
capture() runs at start-up and keeps the first ad visit (an ad visit replaces an earlier plain visit). After sign-in,
send() stores it once on the account (server: Customers.note_ad), so Admin -> Ads can count sign-ups, buyers and
revenue per source, campaign and landing page. Admin -> Ads also builds these links.
"""
import anvil.js
import anvil.server
from anvil.js import window

from . import state

KEY = "sm.ad"
KEEP_DAYS = 60
TAGS = ("source", "medium", "campaign", "content")


def _params():
    out = {}
    for text in (window.location.search or "", (window.location.hash or "").partition("?")[2]):
        if not text:
            continue
        q = anvil.js.new(window.URLSearchParams, text)
        for tag in TAGS:
            v = q.get("utm_" + tag)
            if v:
                out[tag] = str(v)[:120]
        if q.get("gclid") and "source" not in out:
            out["source"] = "google"
        if q.get("fbclid") and "source" not in out:
            out["source"] = "meta"
    return out


def _now_ms():
    return float(window.Date.now())


def capture():
    try:
        tags = _params()
        old = state.store_get(KEY) or {}
        fresh = isinstance(old, dict) and old.get("t") and _now_ms() - float(old["t"]) < KEEP_DAYS * 86400000
        if fresh and (old.get("source") or not tags):
            return                                   # first touch wins; a later ad only replaces a plain visit
        page = (window.location.hash or "#landing").partition("?")[0][:80]
        ref = ""
        try:
            r = str(window.document.referrer or "")
            host = anvil.js.new(window.URL, r).hostname if r else ""
            ref = "" if host == window.location.hostname else host
        except Exception:
            ref = ""
        rec = dict(tags, page=page, ref=ref, first=str(window.Date().toISOString())[:10], t=_now_ms(), sent=False)
        if not tags and ref:
            rec["source"] = ref                       # organic: the referring site (google.com, facebook.com ...)
        state.store_set(KEY, rec)
    except Exception:
        pass


def current():
    v = state.store_get(KEY) or {}
    return v if isinstance(v, dict) else {}


def send():
    """Once per browser after sign-in: remember the first touch on the account (quiet, never blocks anything)."""
    rec = current()
    if not rec or rec.get("sent") or not state.me():
        return
    try:
        anvil.server.call_s("note_ad", {k: rec.get(k) for k in ("source", "medium", "campaign", "content", "page", "ref", "first")})
        rec["sent"] = True
        state.store_set(KEY, rec)
    except Exception:
        pass
