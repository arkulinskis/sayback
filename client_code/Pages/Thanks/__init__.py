from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import ThanksTemplate
from ... import i18n, router, shop, state

TRIES, EVERY = 36, 2500     # ~90 seconds of checking


class Thanks(ThanksTemplate):
    """#thanks/<product>: where Stripe sends people after paying (the Payment Link's success address). It checks every
    2.5 s until the webhook has unlocked the purchase, then offers the first new lesson."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.product = args[0] if args else (state.store_get("sayback.pending") or "")
        self.course = shop.COURSE_OF.get(self.product, "en-es")
        self.tries, self.timer = 0, None
        self.heading.text = i18n.t("Unlocking your lessons")
        self.text.text = i18n.t("Stripe has your payment. This usually takes a few seconds.")
        state.heading(self.heading, 1)
        state.live(self.text)
        self.done_art.visible = False
        self._check()

    def _check(self):
        self.timer = None
        try:
            r = anvil.server.call_s("has_product", self.product)
        except Exception:
            r = {"owned": False}
        if r.get("owned"):
            self._done()
            return
        self.tries += 1
        if self.tries >= TRIES:
            self.heading.text = i18n.t("Almost there")
            self.text.text = i18n.t("Your payment went through, but the unlock is taking longer than usual. It will appear in your library shortly. If it hasn't within an hour, write to arkvital@outlook.com and we'll sort it out the same day.")
            self.waiting_art.visible = False
            return
        self.timer = window.setTimeout(anvil.js.report_exceptions(self._check), EVERY)

    def _done(self):
        state.store_set("sayback.pending", "")
        self.waiting_art.visible = False
        self.done_art.visible = True
        self.heading.text = i18n.t("You're in. Welcome to Sayback.")
        upgrade = self.product.endswith("up") or self.product.endswith("all")
        self.text.text = (i18n.t("Every level is unlocked. Your next lesson is waiting in the library.") if upgrade else
                          i18n.t("All 30 lessons of Level 1 are yours. Tomorrow's drive is lesson 2."))
        self.start_button.text = i18n.t("Play my next lesson")
        self.start_button.visible = True
        state.set_attr(self.lib_link, "href", router.href("home", self.course))

    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        router.go("home", self.course)

    def leave(self):
        if self.timer is not None:
            window.clearTimeout(self.timer)
            self.timer = None
