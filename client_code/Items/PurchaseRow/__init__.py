from anvil import *

from ._anvil_designer import PurchaseRowTemplate
from ... import i18n, state

KINDS = {"level": "One level", "complete": "Levels 1 to 5", "upgrade": "Levels 2 to 5", "bundle": "Every language"}


class PurchaseRow(PurchaseRowTemplate):
    """One purchase on the profile page. item = a purchase dict from my_purchases."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        lv = it.get("levels") or []
        what = i18n.t("Level {n}").replace("{n}", str(lv[0])) if it["kind"] == "level" and lv else i18n.t(KINDS.get(it["kind"], it["kind"]))
        self.what.text = "%s · %s" % (it["course_name"], what)
        how = {"stripe": i18n.t("Paid"), "admin": i18n.t("A gift"), "gift": i18n.t("A gift")}.get(it["source"], it["source"])
        self.meta.text = "%s · %s" % (how, state.short_date(it["created"]))
        if it["refunded"]:
            self.badge.text, self.badge.visible = i18n.t("Refunded"), True
