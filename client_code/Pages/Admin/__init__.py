from anvil import *
import anvil.media
from anvil.js import window

from ._anvil_designer import AdminTemplate
from ... import state

TABS = ["overview", "sales", "waitlist", "shop", "feedback", "users", "demo"]
PRODUCTS = ["es1", "esall", "esup", "en1", "enall", "enup"]
PRODUCT_NAMES = [("Sayback Spanish · Level 1", "es1"), ("Sayback Spanish · Levels 1-5", "esall"),
                 ("Sayback Spanish · Levels 2-5", "esup"), ("Sayback Inglés · Level 1", "en1"),
                 ("Sayback Inglés · Levels 1-5", "enall"), ("Sayback Inglés · Levels 2-5", "enup")]


class Admin(AdminTemplate):
    """#admin/<tab>: overview (sales, listening, the setup checklist), sales (purchases, refunds, giving a course),
    the waitlist (CSV), Shop & setup (prices, Stripe Payment Links, webhook, lesson audio), the old feedback inbox,
    users and the demo data. Each tab is its own address, so the browser's back button works. Admin is English only."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.tab = args[0] if args and args[0] in TABS else "overview"
        self._filter = "new"
        parts = {"overview": self.overview_part, "sales": self.sales_part, "waitlist": self.waitlist_part,
                 "shop": self.shop_part, "feedback": self.feedback_part, "users": self.users_part, "demo": self.demo_part}
        tabs = {"overview": self.tab_overview, "sales": self.tab_sales, "waitlist": self.tab_waitlist, "shop": self.tab_shop,
                "feedback": self.tab_feedback, "users": self.tab_users, "demo": self.tab_demo}
        for name in TABS:
            parts[name].visible = name == self.tab
            tabs[name].classes["on"] = name == self.tab
        self.feedback_panel.add_event_handler("x-changed", self._feedback_changed)
        self.wait_panel.add_event_handler("x-changed", self._waitlist_changed)
        getattr(self, "_" + self.tab)()

    # ---- overview
    def _overview(self):
        d = state.call("admin_overview")
        shop, lis = d["shop"], d["listening"]
        self.s_revenue.text = "%s%s" % (shop["currency"], "{:,.0f}".format(shop["revenue_cents"] / 100.0))
        self.s_buyers.text, self.s_waitlist.text = str(shop["buyers"]), str(shop["waitlist"])
        self.s_users.text = str(d["users"])
        self.s_listeners.text, self.s_minutes.text = str(lis["listeners_week"]), "{:,}".format(lis["minutes_week"])
        self.demo_line.text = "Demo data is %s (%d demo people). Manage it in the Demo data tab." % (
            d["demo"]["state"], d["demo"]["counts"].get("users", 0))
        s = state.call("admin_shop")
        audio = s["status"]["audio"]
        links = len([p for p in s["products"] if p["link"]])
        self._check(self.chk_audio, self.chk_audio_text, audio == "r2",
                    {"r2": "Lesson audio: private R2 bucket connected.",
                     "public": "Lesson audio: a public test address is set. Switch to the private R2 bucket before selling.",
                     "none": "Lesson audio: not connected yet, so lessons can't play."}[audio])
        self._check(self.chk_links, self.chk_links_text, links == 6,
                    "Stripe Payment Links: %d of 6 set. %s" % (links, "Buy buttons go to Stripe." if links else
                                                              "Until then, buy buttons collect waitlist emails."))
        self._check(self.chk_webhook, self.chk_webhook_text, s["status"]["stripe_webhook_secret"],
                    "Stripe webhook secret: %s" % ("set. Payments unlock lessons by themselves." if s["status"]["stripe_webhook_secret"]
                                                   else "missing. Payments won't unlock anything until it's set."))

    def _check(self, row, label, good, text):
        row.classes["good"] = bool(good)
        row.classes["bad"] = not good
        label.text = text

    # ---- sales
    def _sales(self):
        d = state.call("admin_sales")
        self.sales_panel.items = d["purchases"]
        self.no_sales.visible = not d["purchases"]
        money = ", ".join("%s %s" % (r["currency"] or "", "{:,.2f}".format(r["cents"] / 100.0)) for r in d["revenue"]) or "nothing yet"
        self.sales_line.text = "%s · %s · revenue %s · %d refunded" % (
            state.plural(d["total"], "purchase"), state.plural(d["buyers"], "buyer"), money, d["refunded"])
        self.grant_product.items = PRODUCT_NAMES
        state.set_control_attr(self.grant_product, "aria-label", "What to give")

    @handle("grant_button", "click")
    def grant_button_click(self, **event_args):
        r = state.call("admin_grant", self.grant_email.text, self.grant_product.selected_value, self.grant_note.text)
        if r:
            state.toast("Given. " + ("It's in their library now." if r["has_account"] else
                                     "It joins their account when they sign up with that email."), "ok")
            self.grant_email.text = self.grant_note.text = ""
            self._sales()

    # ---- waitlist
    def _waitlist(self):
        d = state.call("admin_waitlist")
        self._csv = d["csv"]
        self.wait_panel.items = d["items"]
        self.no_wait.visible = not d["items"]
        self.wait_line.text = state.plural(d["total"], "email") + " on the list"

    def _waitlist_changed(self, **event_args):
        self._waitlist()

    @handle("csv_button", "click")
    def csv_button_click(self, **event_args):
        anvil.media.download(BlobMedia("text/csv", self._csv.encode("utf-8"), name="sayback-waitlist.csv"))

    # ---- shop & setup
    def _shop(self):
        s = state.call("admin_shop")
        st = s["settings"]
        self.price_level1.text = st["prices"]["level1"]
        self.price_complete.text = st["prices"]["complete"]
        self.price_upgrade.text = st["prices"]["upgrade"]
        self.currency.text, self.currency_code.text = st["currency"], st["currency_code"]
        self.guarantee_days.text, self.free_lessons.text = st["guarantee_days"], s["free_lessons"]
        for p in s["products"]:
            getattr(self, "link_" + p["product"]).text = p["link"]
            getattr(self, "ok_" + p["product"]).text = "After payment, redirect to: " + p["success_url"]
        self.webhook_url.text = s["webhook_url"]
        self.webhook_status.text = ("Signing secret: set." if s["status"]["stripe_webhook_secret"]
                                    else "Signing secret: not set yet (App Secrets > stripe_webhook_secret).")
        self.webhook_status.role = "msg-note" if s["status"]["stripe_webhook_secret"] else "msg-error"
        audio = s["status"]["audio"]
        self.audio_status.text = {"r2": "Connected: private Cloudflare R2 bucket (signed links).",
                                  "public": "Test mode: lessons play from the public test address below.",
                                  "none": "Not connected yet: lessons can't play."}[audio]
        self.audio_status.role = "msg-note" if audio == "r2" else "msg-error"
        self.audio_base.text = s["audio_base"]

    @handle("shop_save_button", "click")
    def shop_save_button_click(self, **event_args):
        data = {"prices": {"level1": self.price_level1.text, "complete": self.price_complete.text,
                           "upgrade": self.price_upgrade.text},
                "links": {p: (getattr(self, "link_" + p).text or "").strip() for p in PRODUCTS},
                "currency": self.currency.text, "currency_code": self.currency_code.text,
                "guarantee_days": self.guarantee_days.text, "free_lessons": self.free_lessons.text,
                "audio_base": (self.audio_base.text or "").strip()}
        if state.call("admin_save_shop", data):
            state.toast("Saved", "ok")
            self._shop()

    @handle("audio_test_button", "click")
    def audio_test_button_click(self, **event_args):
        r = state.call("admin_audio_test", "en-es")
        if r and r["url"]:
            window.open(r["url"], "_blank", "noopener")
        elif r:
            state.toast("Audio isn't connected yet: set the r2_url App Secret or a test address, then Save.", "error")

    # ---- feedback
    def _feedback(self):
        d = state.call("list_feedback", None)
        self._fb = d
        items = [i for i in d["items"] if self._filter == "all" or i["status"] == self._filter]
        self.feedback_panel.items = items
        self.no_feedback.visible = not items
        labels = {"new": "New", "read": "Read", "done": "Done", "all": "All"}
        for key, el in (("new", self.f_new), ("read", self.f_read), ("done", self.f_done), ("all", self.f_all)):
            n = len(d["items"]) if key == "all" else d["counts"].get(key, 0)
            el.text = "%s (%d)" % (labels[key], n)
            el.role = ["seg", "on"] if key == self._filter else ["seg"]

    def _set_filter(self, value):
        self._filter = value
        self._feedback()

    @handle("f_new", "click")
    def f_new_click(self, **event_args):
        self._set_filter("new")

    @handle("f_read", "click")
    def f_read_click(self, **event_args):
        self._set_filter("read")

    @handle("f_done", "click")
    def f_done_click(self, **event_args):
        self._set_filter("done")

    @handle("f_all", "click")
    def f_all_click(self, **event_args):
        self._set_filter("all")

    def _feedback_changed(self, **event_args):
        self._feedback()

    # ---- users
    def _users(self, query=None):
        d = state.call("list_users", query or None)
        self.users_panel.items = d["users"]
        self.users_count.text = state.plural(d["total"], "person", "people")

    @handle("search_box", "pressed_enter")
    def search_box_pressed_enter(self, **event_args):
        self._users(self.search_box.text)

    @handle("search_button", "click")
    def search_button_click(self, **event_args):
        self._users(self.search_box.text)

    # ---- demo data
    def _demo(self):
        d = state.call("admin_overview")["demo"]
        counts = ", ".join("%s %s" % (v, k) for k, v in d["counts"].items())
        self.demo_status.text = "Status: %s · %s" % (d["state"], counts)
        self.demo_load_button.text = "Reload demo data" if d["state"] == "loaded" else "Load demo data"

    @handle("demo_load_button", "click")
    def demo_load_button_click(self, **event_args):
        if confirm("Demo people and content are added (any old demo rows are replaced).", title="Load the demo data?",
                   buttons=[("Cancel", False), ("Load", True)], role="app-dialog"):
            if state.call("demo_load"):
                state.toast("Done", "ok")
                self._demo()

    @handle("demo_remove_button", "click")
    def demo_remove_button_click(self, **event_args):
        if confirm("Every demo row is deleted. Real data stays.", title="Remove the demo data?",
                   buttons=[("Cancel", False), ("Remove", True)], role="app-dialog"):
            if state.call("demo_remove"):
                state.toast("Done", "ok")
                self._demo()
