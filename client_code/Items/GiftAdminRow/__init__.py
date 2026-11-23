from anvil import *

from ._anvil_designer import GiftAdminRowTemplate
from ... import state


class GiftAdminRow(GiftAdminRowTemplate):
    """One gift in Admin -> Gifts: what, code, who bought it, for whom, opened by whom."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.what.text = it["label"] + ((" · for " + it["to_name"]) if it["to_name"] else "")
        bits = ["code " + it["nice"], "from " + (it["buyer_email"] or "?"), state.short_date(it["created"])]
        if it["amount"]:
            bits.append("%s %s" % (it["currency"], "{:,.2f}".format(it["amount"] / 100.0)))
        if it["redeemed_email"]:
            bits.append("opened by " + it["redeemed_email"])
        self.meta.text = " · ".join(bits) + (" · demo" if it["demo"] else "")
        self.badge.text = "Refunded" if it["refunded"] else ("Opened" if it["redeemed"] else "Waiting")
