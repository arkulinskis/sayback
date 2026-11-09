from anvil import *

from ._anvil_designer import PurchaseRowTemplate
from ... import i18n, state

KINDS = {"level1": "Level 1", "complete": "Levels 1 to 5", "upgrade": "Levels 2 to 5"}


class PurchaseRow(PurchaseRowTemplate):
    """One purchase on the profile page. item = a purchase dict from my_purchases."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.what.text = "%s · %s" % (it["course_name"], i18n.t(KINDS.get(it["kind"], it["kind"])))
        how = {"stripe": i18n.t("Paid"), "admin": i18n.t("A gift"), }.get(it["source"], it["source"])
        self.meta.text = "%s · %s" % (how, state.short_date(it["created"]))
        if it["refunded"]:
            self.badge.text, self.badge.visible = i18n.t("Refunded"), True
