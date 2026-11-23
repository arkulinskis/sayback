from anvil import *

from ._anvil_designer import AdRowTemplate


class AdRow(AdRowTemplate):
    """One source / campaign / landing page in Admin -> Ads. item from admin_ads: signups, buyers, conversion, revenue."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.what.text = " · ".join(x for x in (it["source"], it["campaign"], it["page"]) if x)
        self.signups.text = str(it["signups"])
        self.buyers.text = str(it["buyers"])
        self.conv.text = "%s%%" % it["conversion"]
        self.revenue.text = "$%s" % "{:,.0f}".format(it["revenue_cents"] / 100.0)
