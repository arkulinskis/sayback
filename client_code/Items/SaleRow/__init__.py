from anvil import *

from ._anvil_designer import SaleRowTemplate
from ... import state

KINDS = {"level1": "Level 1", "complete": "Levels 1-5", "upgrade": "Levels 2-5"}


class SaleRow(SaleRowTemplate):
    """One purchase in Admin -> Sales. Refund locks the lessons again (do the money refund in Stripe; a Stripe
    refund also arrives here by itself through the webhook)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._draw()

    def _draw(self):
        it = self.item
        self.who.text = it.get("name") or it["email"].split("@")[0]
        self.email.text = it["email"] + ("  ·  demo" if it.get("demo") else "")
        self.what.text = "%s · %s%s" % (it["course_name"], KINDS.get(it["kind"], it["kind"]),
                                        "" if it["source"] == "stripe" else " · " + (it["note"] or it["source"]))
        self.amount.text = ("%s %.2f" % (it["currency"], it["amount"] / 100.0)) if it["amount"] else ("gift" if it["source"] == "admin" else "")
        self.when.text = state.short_date(it["created"])
        self.refund_button.text = "Unlock again" if it["refunded"] else "Mark refunded"
        self.classes["refunded"] = bool(it["refunded"])

    @handle("refund_button", "click")
    def refund_button_click(self, **event_args):
        flag = not self.item["refunded"]
        if flag and not confirm("Their lessons lock again. Refund the money itself in Stripe.", title="Mark as refunded?",
                                buttons=[("Cancel", False), ("Mark refunded", True)], role="app-dialog"):
            return
        r = state.call("admin_set_refunded", self.item["id"], flag)
        if r:
            self.item = r["purchase"]
            self._draw()
