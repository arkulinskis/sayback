from anvil import *

from ._anvil_designer import LinkRowTemplate
from ... import state


class LinkRow(LinkRowTemplate):
    """One Stripe Payment Link box in Admin -> Shop & setup. item = {product, course_name, kind, link, success_url}.
    The page reads link_box.text from every row when it saves."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.name.text = it["course_name"]
        self.link_box.text = it["link"] or ""
        self.ok.text = "After payment, redirect to: " + it["success_url"]
        state.set_control_attr(self.link_box, "aria-label", "Payment Link: " + it["course_name"])
