from anvil import *

from ._anvil_designer import GiftRowTemplate
from ... import router, state


class GiftRow(GiftRowTemplate):
    """One gift I bought (Gift page). item = a card dict from my_gifts: label, to_name, code, redeemed, refunded."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.what.text = ("For %s: " % it["to_name"] if it["to_name"] else "") + it["label"]
        self.meta.text = "Bought %s · code %s" % (state.short_date(it["created"]), it["nice"])
        if it["refunded"]:
            self.badge.text, self.badge.visible = "Refunded", True
        elif it["redeemed"]:
            self.badge.text, self.badge.visible = "Opened", True
        state.set_attr(self.open_link, "href", router.href("gift", "card", it["code"]))
        state.set_attr(self.open_link, "aria-label", "Gift card for %s" % (it["to_name"] or it["label"]))
