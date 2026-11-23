from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import GiftTemplate
from ... import courses, i18n, shop, state


class Gift(GiftTemplate):
    """#gift[/<course>]: the gift sales page (pick a language, then Level 1 / the complete course / every language as
    a gift) plus "Your gifts" for signed-in givers. #gift/card/<code>: the giver's card: name + message, print, copy
    the redeem link. Buying = shop.buy(product, gift=True); the webhook makes the code (server_code/Gifts.py)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        if len(args) > 1 and args[0] == "card":
            self.sell_part.visible = False
            self._card(args[1])
            return
        self.card_part.visible = False
        self.course = args[0] if args and args[0] in courses.COURSES else "en-it"
        for code, el in (("en-es", self.g_es), ("en-fr", self.g_fr), ("en-it", self.g_it), ("es-en", self.g_en)):
            el.classes["on"] = code == self.course
        s = shop.info(self.course) or {}
        offers = s.get("gifts") or []
        self.offers.items = [dict(p, currency=s.get("currency") or "$", course=self.course, best=p["kind"] == "complete",
                                  picked=False) for p in offers]
        if offers and not any(p["open"] for p in offers):
            self.closed_note.text = "Gift cards open with the shop, very soon. The buttons put you on the list for opening day."
            self.closed_note.visible = True
        self.mine_part.visible = False
        if state.me():
            r = state.call_quiet("my_gifts") or {}
            gifts = r.get("gifts") or []
            self.mine.items = gifts
            self.mine_part.visible = bool(gifts)

    # ---------------------------------------------------------------- one card
    def _card(self, code):
        self.code = code
        self.g = {}
        if not state.me():
            self.card_state.text = "Sign in to see this gift card."
            self.card_state.visible = True
            self.card.visible = self.edit_part.visible = False
            return
        r: dict = {}
        try:
            r = anvil.server.call("gift_card", code)
        except anvil.server.AppOfflineError:
            r = {"ok": False, "error": "You're offline. Connect to see this gift card."}
        if not r.get("ok"):
            self.card_state.text = str(r.get("error") or "That gift isn't in your account.")
            self.card_state.visible = True
            self.card.visible = self.edit_part.visible = False
            return
        self.g: dict = dict(r["gift"])
        state.heading(self.card_heading, 1)
        self._draw()
        self.to_box.text = self.g["to_name"]
        self.msg_box.text = self.g["message"]
        state.set_control_attr(self.to_box, "maxlength", "60")
        state.set_control_attr(self.msg_box, "maxlength", "280")
        if self.g["redeemed"] or self.g["refunded"]:
            self.card_state.text = ("Opened %s. It's in their library now." % (self.g.get("redeemed_at") or "")[:10]
                                    if self.g["redeemed"] else "This gift was refunded.")
            self.card_state.visible = True
            self.save_button.visible = False

    def link(self):
        origin = str(window.location.origin)
        return "%s/#redeem/%s" % (origin, self.g["code"])

    def _draw(self):
        g = self.g
        self.gc_to.text = ("For " + g["to_name"]) if g["to_name"] else "For you"
        self.gc_what.text = g["label"] + ", yours for life"
        self.gc_msg.text = ("“%s”" % g["message"]) if g["message"] else ""
        self.gc_msg.visible = bool(g["message"])
        self.gc_link.text = self.link().replace("https://", "").replace("http://", "")
        self.gc_code.text = g["nice"]

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        r = state.call("set_gift_note", self.code, self.to_box.text or "", self.msg_box.text or "")
        if r:
            self.g = r["gift"]
            self._draw()
            state.toast("Card saved.", "ok")

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        window.print()

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        text = "%s\n%s" % (("A gift for you, " + self.g["to_name"] + ": ") if self.g["to_name"] else "A gift for you: ",
                           self.link())
        try:
            window.navigator.clipboard.writeText(text)
            state.toast("Link copied. Paste it into a text or an email.", "ok")
        except Exception:
            alert(self.link(), title="Copy this link")
