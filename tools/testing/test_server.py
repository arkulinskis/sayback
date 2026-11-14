"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
assert ana["last_seen"] is not None
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- feedback
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#home", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and fb["email"] == "guest@example.com" and "evil" not in fb["context"] and fb["status"] == "new"
for i in range(4):
    ok(call("submit_feedback", "idea", "Idea number %d" % i))
bad(call("submit_feedback", "idea", "One too many this hour"), "rate limit")
as_user(ana)
ok(call("submit_feedback", "nonsense-kind", "Signed-in feedback"))
assert T.feedback.get(message="Signed-in feedback")["kind"] == "other"
assert denied("list_feedback")
as_user(admin)
lst = call("list_feedback")
assert lst["counts"]["new"] == 6 and len(lst["items"]) == 6
fid = lst["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
assert call("list_feedback", "done")["items"][0]["note"] == "Fixed it"
bad(call("set_feedback_status", fid, "weird"))
bad(call("set_feedback_status", "nope", "done"))
ok(call("delete_feedback", fid))
assert len(call("list_feedback")["items"]) == 5

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("demo_load", ()), ("demo_remove", ())]:
    assert denied(fn, *args), fn
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 3 and ov["admins"] == 1 and ov["feedback_new"] == 5
assert len(call("list_users")["users"]) == 3 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
assert bob["is_admin"] is True
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
assert bob["enabled"] is False
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))
assert bob["is_admin"] is False

# ---------------------------------------------------------------------------------- Sayback: catalog + access
import hashlib as _h, hmac as _hm, time as _t
import anvil.secrets as _sec
Cat, Shop, L, A = M["Catalog"], M["Shop"], M["Listening"], M["Audio"]
assert len(Cat.lessons("en-es")) == 150 and len(Cat.lessons("es-en")) == 150
assert all(len(x["pairs"]) == 20 for x in Cat.lessons("en-es")), "20 new sentences in every lesson"
assert Cat.neighbours("en-es", "L1-01") == (None, "L1-02") and Cat.neighbours("en-es", "L5-30")[1] is None
assert Cat.is_free("L1-01") and not Cat.is_free("L1-02")
carla = person("carla@example.com", "Carla")
as_user(None)
assert denied("library") and denied("get_lesson", "en-es", "L1-01") and denied("save_progress", "en-es", "L1-01", 10)
as_user(carla)
lib = call("library", None, None, now.date().isoformat())
assert lib["course"] == "en-es" and len(lib["lessons"]) == 30 and lib["lessons"][0]["state"] == "open"
assert lib["lessons"][1]["state"] == "locked" and lib["next"]["code"] == "L1-01" and lib["stats"]["streak"] == 0
assert M["DemoData"].state() == "loaded", "demo loads on first library visit"
les = ok(call("get_lesson", "en-es", "L1-01"))
assert les["locked"] == "" and les["url"] is None and les["audio"] is False, "no storage set up yet: no link"
assert len(les["pairs"]) == 20 and les["next"]["code"] == "L1-02" and les["next"]["locked"]
lk = ok(call("get_lesson", "en-es", "L1-02"))
assert lk["locked"] == "level1" and len(lk["pairs"]) == 3 and lk["url"] is None, "locked: a taste of 3 sentences, no audio"
assert ok(call("get_lesson", "en-es", "L2-01"))["locked"] == "complete"
bad(call("get_lesson", "en-es", "L9-99"))
bad(call("get_lesson", "xx-yy", "L1-01"))

# audio: a public test address, then private R2 links
as_user(admin)
ok(call("admin_save_shop", {"audio_base": "https://media.example.com/sb"}))
as_user(carla)
assert ok(call("get_lesson", "en-es", "L1-01"))["url"] == "https://media.example.com/sb/en-es/L1/L1-01.mp3"
_sec.SECRETS["r2_url"] = "r2://AKIDEXAMPLE:secretKEY@acc123/sayback-audio"
les = ok(call("get_lesson", "es-en", "L1-01"))
assert les["url"].startswith("https://acc123.r2.cloudflarestorage.com/sayback-audio/es-en/L1/L1-01.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256")
assert "response-content-disposition=attachment" in les["download"] and les["transcript"].split("?")[0].endswith("L1-01.txt")
assert A.parse_r2("r2://nope") is None and A.status() == "r2"
cfg = {"key": "AKIAIOSFODNN7EXAMPLE", "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "host": "examplebucket.s3.amazonaws.com", "region": "us-east-1"}
assert A.presign(cfg, "GET", "/test.txt", 86400, when=dt.datetime(2013, 5, 24, tzinfo=dt.timezone.utc)).endswith(
    "X-Amz-Signature=aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"), "AWS's own presign example"

# progress + streak
bad(call("save_progress", "en-es", "L1-02", 100, 30), "locked lessons don't save")
ok(call("save_progress", "en-es", "L1-01", 600, 60, False, now.date().isoformat()))
ok(call("save_progress", "en-es", "L1-01", 620, 9999, False, now.date().isoformat()))  # listened is capped at 120
lib = call("library", "en-es", 1, now.date().isoformat())
assert lib["lessons"][0]["state"] == "started" and lib["next"]["position"] == 620 and lib["stats"]["today_minutes"] == 3
assert lib["stats"]["streak"] == 1
T.listening.add_row(user=carla, course="en-es", day=now.date() - dt.timedelta(days=1), seconds=900, is_demo=False)
T.listening.add_row(user=carla, course="en-es", day=now.date() - dt.timedelta(days=3), seconds=900, is_demo=False)
assert call("library", "en-es", 1, now.date().isoformat())["stats"]["streak"] == 2, "a gap ends the streak"
r = ok(call("save_progress", "en-es", "L1-01", 2600, 60, False, now.date().isoformat()))
assert r["done"] and r["newly_done"]
ok(call("save_progress", "en-es", "L1-01", 2650, 30, False, now.date().isoformat()))
pr = T.progress.get(user=carla, course="en-es", code="L1-01")
assert pr["completions"] == 1 and pr["position"] == 0, "a finish counts once, and the next play starts at the top"
assert call("library", "en-es", 1, now.date().isoformat())["lessons"][0]["state"] == "done"
ok(call("set_done", "en-es", "L1-01", False))
assert not T.progress.get(user=carla, course="en-es", code="L1-01")["done"]
bad(call("set_done", "en-es", "L3-01", True))

# shop: closed -> waitlist, then Payment Links
info = ok(call("shop_info", "en-es"))
assert [p["kind"] for p in info["products"]] == ["level1", "complete"] and not any(p["open"] for p in info["products"])
bad(call("shop_info", "zz"))
assert ok(call("checkout", "es1"))["waitlist"] is True
bad(call("checkout", "nope"))
as_user(None)
assert denied("checkout", "es1")
bad(call("join_waitlist", "not-an-email", "en-es"))
ok(call("join_waitlist", "fan@example.com", "en-es", "landing"))
assert ok(call("join_waitlist", "FAN@example.com", "en-es"))["already"] is True
as_user(admin)
bad(call("admin_save_shop", {"links": {"es1": "http://not-secure"}}))
bad(call("admin_save_shop", {"prices": {"level1": "free"}}))
sh = ok(call("admin_save_shop", {"links": {"es1": "https://buy.stripe.com/test_es1", "esall": "https://buy.stripe.com/test_esall"},
                                  "prices": {"level1": 35}, "free_lessons": 2}))
assert sh["settings"]["prices"]["level1"] == 35 and sh["free_lessons"] == 2
assert sh["products"][0]["success_url"].endswith("/#thanks/es1") and sh["webhook_url"].endswith("/_/api/stripe")
as_user(carla)
assert ok(call("get_lesson", "en-es", "L1-02"))["locked"] == "", "free lessons follow the setting"
url = ok(call("checkout", "es1"))["url"]
ref = "%s-es1" % Shop.user_ref(carla)
assert url.startswith("https://buy.stripe.com/test_es1?client_reference_id=" + ref) and "prefilled_email=carla%40example.com" in url
assert Shop.user_from_ref(Shop.user_ref(carla)) == carla and Shop.user_from_ref("x") is None

# webhook: signature, grant, duplicate, refund
secret = "whsec_test"
body = json.dumps({"type": "checkout.session.completed", "data": {"object": {
    "id": "cs_1", "client_reference_id": ref, "payment_status": "paid", "amount_total": 3500, "currency": "usd",
    "payment_intent": "pi_1", "customer_details": {"email": "carla@example.com"}}}}).encode()
ts = int(_t.time())
sig = "t=%d,v1=%s" % (ts, _hm.new(secret.encode(), str(ts).encode() + b"." + body, _h.sha256).hexdigest())
assert Shop.verify(body, sig, secret) and not Shop.verify(body + b" ", sig, secret) and not Shop.verify(body, sig, "other")
assert not Shop.verify(body, sig, secret, now=ts + 999), "old signatures are refused"
anvil.server.request.body, anvil.server.request.headers = body, {"Stripe-Signature": sig}
assert anvil.server.ENDPOINTS["/stripe"]().status == 503, "no secret set yet"
_sec.SECRETS["stripe_webhook_secret"] = secret
res = anvil.server.ENDPOINTS["/stripe"]()
assert res.status == 200 and json.loads(res.body)["result"] == "granted", res.body
assert json.loads(anvil.server.ENDPOINTS["/stripe"]().body)["result"] == "duplicate"
anvil.server.request.headers = {"Stripe-Signature": "t=%d,v1=bad" % ts}
assert anvil.server.ENDPOINTS["/stripe"]().status == 400
assert Cat.owned_levels(carla, "en-es") == {1}
assert call("has_product", "es1")["owned"] and not call("has_product", "esall")["owned"]
lib = call("library", "en-es", 1, now.date().isoformat())
assert lib["lessons"][5]["state"] == "open" and lib["lessons"][0]["state"] != "locked"
assert [p["kind"] for p in lib["shop"]["products"]] == ["level1", "upgrade"], "Level 1 owners see the upgrade"
bad(call("checkout", "es1"), "already owned")
assert len(call("my_purchases")["purchases"]) == 1
assert Shop.handle_event({"type": "checkout.session.completed", "data": {"object": {"id": "cs_2", "payment_status": "unpaid",
                                                                                  "client_reference_id": ref}}}) == "waiting"
assert Shop.handle_event({"type": "checkout.session.completed", "data": {"object": {"id": "cs_3", "payment_status": "paid",
                                                                                  "client_reference_id": "1_2-bogus"}}}) == "unknown product"
assert Shop.handle_event({"type": "charge.refunded", "data": {"object": {"payment_intent": "pi_1", "refunded": False}}}) == "partial refund ignored"
assert Shop.handle_event({"type": "charge.refunded", "data": {"object": {"payment_intent": "pi_1", "refunded": True}}}) == "refunded 1"
assert Cat.owned_levels(carla, "en-es") == set(), "a refund locks the levels again"
assert Shop.handle_event({"type": "invoice.paid"}) == "ignored"

# admin: sales, grants (also before the account exists), refunds, waitlist, audio test
as_user(carla)
for fn, args in [("admin_shop", ()), ("admin_save_shop", ({},)), ("admin_sales", ()), ("admin_grant", ("a@b.co", "es1")),
                 ("admin_waitlist", ()), ("admin_audio_test", ()), ("admin_set_refunded", ("x", True))]:
    assert denied(fn, *args), fn
as_user(admin)
sales = call("admin_sales")
assert sales["total"] >= 1 and sales["refunded"] >= 1 and sales["purchases"][0]["email"]
carla_buy = [p for p in sales["purchases"] if p["email"] == "carla@example.com"][0]
ok(call("admin_set_refunded", carla_buy["id"], False))
assert Cat.owned_levels(carla, "en-es") == {1}
bad(call("admin_grant", "nope", "esall"))
bad(call("admin_grant", "dora@example.com", "zzz"))
assert ok(call("admin_grant", "dora@example.com", "enall"))["has_account"] is False
dora = person("dora@example.com", "Dora")
as_user(dora)
call("get_me")
assert Cat.owned_levels(dora, "es-en") == {1, 2, 3, 4, 5}, "a gift waiting for an email joins the new account"
assert ok(call("get_lesson", "es-en", "L5-30"))["locked"] == ""
as_user(admin)
wl = call("admin_waitlist")
assert any(i["email"] == "fan@example.com" for i in wl["items"]) and "fan@example.com" in wl["csv"] and "demo@example.com" not in wl["csv"]
ok(call("admin_waitlist_remove", [i for i in wl["items"] if i["email"] == "fan@example.com"][0]["id"]))
assert ok(call("admin_audio_test"))["url"].startswith("https://acc123.r2")
ov = call("admin_overview")
assert ov["shop"]["sales"] >= 1 and ov["listening"]["minutes_week"] >= 1 and ov["shop"]["shop_open"]
assert ok(call("get_lesson", "en-es", "L4-10"))["locked"] == "", "admins hear everything"

# demo data
ok(call("demo_remove"))
assert M["DemoData"].state() == "removed" and not T.users.search(is_demo=True) and not T.purchases.search(is_demo=True)
assert T.purchases.get(email="carla@example.com") is not None, "removing demo data keeps real data"
as_user(carla)
call("library")
assert M["DemoData"].state() == "removed", "removed demo data doesn't come back by itself"
as_user(admin)
ok(call("demo_load"))
ok(call("demo_load"))
assert len(T.users.search(is_demo=True)) == len(M["DemoData"].DEMO_USERS), "reloading replaces the demo instead of doubling it"

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup" and call("legal_state")["accepted_version"] == st["version"]

# ---------------------------------------------------------------------------------- schema check (App Board): names only, never data
r = anvil.server.ENDPOINTS["/schema-check"](tables="users, purchases,no_such_table")
json.dumps(r)
assert "email" in r["tables"]["users"] and "product" in r["tables"]["purchases"] and r["tables"]["no_such_table"] is None, r

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"session_ping", "get_me", "submit_feedback", "legal_state", "legal_accept", "shop_info", "join_waitlist"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
