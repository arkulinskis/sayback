from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import WaitlistTemplate
from ... import i18n, state


class Waitlist(WaitlistTemplate):
    """Shown by shop.buy() while no Stripe link is set for a product: one email, one tap. The page's language
    applies (data-t + i18n.t). Closes itself with x-close-alert."""

    def __init__(self, course="en-es", **properties):
        super().__init__(**properties)
        self.course = course
        self.done_part.visible = False
        me = state.me()
        self.email_box.text = (me or {}).get("email") or ""
        state.set_control_attr(self.email_box, "autocomplete", "email")
        for b, text in ((self.close_button, "Not now"), (self.join_button, "Tell me when it opens"), (self.ok_button, "Great")):
            b.text = i18n.t(text)
        i18n.apply(anvil.js.get_dom_node(self))

    @handle("email_box", "pressed_enter")
    def email_box_pressed_enter(self, **event_args):
        self.join_button_click()

    @handle("join_button", "click")
    def join_button_click(self, **event_args):
        r = anvil.server.call("join_waitlist", self.email_box.text, self.course, "app:" + str(window.location.hash)[:60])
        if not r.get("ok"):
            self.message.text = i18n.t(r.get("error") or "That didn't work.")
            self.message.visible = True
            return
        self.ask_part.visible = False
        self.done_part.visible = True

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=False)

    @handle("ok_button", "click")
    def ok_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
