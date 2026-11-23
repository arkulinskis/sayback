from anvil import *

from ._anvil_designer import CustomerRowTemplate
from ... import state


class CustomerRow(CustomerRowTemplate):
    """One account in Admin -> Customers: who, what they own and how (paid / gift / admin), money spent, gifts
    bought, minutes listened, and the ad they first came from."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.who.text = "%s · %s%s" % (it["name"], it["email"], " · demo" if it["demo"] else "")
        owns = ", ".join(it["courses"]) or "free lesson only"
        bits = [owns, "joined " + state.short_date(it["joined"]), "%d min listened" % it["minutes"]]
        if it["how"]:
            bits.insert(1, "/".join(it["how"]))
        if it["gifts_bought"]:
            bits.append(state.plural(it["gifts_bought"], "gift") + " bought")
        self.what.text = " · ".join(bits)
        self.money.text = ("$%s" % "{:,.0f}".format(it["spent_cents"] / 100.0)) if it["spent_cents"] else ""
        self.src.text = " · ".join(x for x in (it["source"], it["campaign"], it["page"]) if x) or "direct"
