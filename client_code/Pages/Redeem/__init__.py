from anvil import *
import anvil.js
import anvil.server

from ._anvil_designer import RedeemTemplate
from ... import i18n, router, state


class Redeem(RedeemTemplate):
    """#redeem/<code>: the gift card someone received. Visitors make a free account first (they come back here),
    members press "Open my gift" and land in their library. #redeem with no code shows a box for the code."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.heading, 1)
        self.code = (args[0] if args else "").strip()
        self.card.visible = self.act_part.visible = False
        if self.code:
            self.code_part.visible = False
            self._look(self.code)
        else:
            state.set_control_attr(self.code_box, "autocomplete", "off")

    def _look(self, code):
        r: dict = {}
        try:
            r = anvil.server.call("gift_public", code)
        except anvil.server.AppOfflineError:
            r = {"ok": False, "error": i18n.t("You're offline. Connect to open your gift.")}
        if not r.get("ok"):
            self._say(str(r.get("error") or i18n.t("We can't find that gift code. Check the letters on the card.")))
            self.code_part.visible = True
            return
        g: dict = dict(r["gift"])
        self.code = g["code"]
        self.code_part.visible = False
        self.card.visible = True
        self.gc_to.text = (i18n.t("For {name}").replace("{name}", g["to_name"])) if g["to_name"] else i18n.t("For you")
        self.gc_what.text = g["label"]
        self.gc_msg.text = ("“%s”" % g["message"]) if g["message"] else ""
        self.gc_msg.visible = bool(g["message"])
        self.gc_from.text = (i18n.t("From {name}").replace("{name}", g["from_name"])) if g["from_name"] else ""
        if g["refunded"]:
            self._say(i18n.t("This gift was refunded, so it can't be opened any more."))
            return
        if g["redeemed"]:
            self._say(i18n.t("This gift has already been opened. If that was you, it's in your library."))
            return
        self.act_part.visible = True
        me = state.me()
        self.open_button.visible = bool(me)
        self.signup_link.visible = self.signin_line.visible = not me
        here = router.href("redeem", self.code)
        if not me:
            router.remember_after(here)

    def _say(self, text):
        self.note.text = text
        self.note.visible = True

    @handle("code_box", "pressed_enter")
    def code_box_pressed_enter(self, **event_args):
        self.look_button_click()

    @handle("look_button", "click")
    def look_button_click(self, **event_args):
        code = (self.code_box.text or "").strip()
        if not code:
            self._say(i18n.t("Type the code from your card."))
            return
        self.note.visible = False
        router.replace("redeem", code)
        self._look(code)

    @handle("open_button", "click")
    def open_button_click(self, **event_args):
        r = state.call("redeem_gift", self.code)
        if not r:
            return
        state.toast(i18n.t("Your gift is open. Enjoy the ride!"), "ok")
        router.go("home", r["course"])
