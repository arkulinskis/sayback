from anvil import *
import anvil.js

from ._anvil_designer import ProductCardTemplate
from ... import i18n, router, shop, state

TITLES = {"level1": "Level 1 · First Steps", "complete": "Complete course · Levels 1 to 5", "upgrade": "Upgrade · Levels 2 to 5"}
BUTTONS = {"level1": "Get Level 1", "complete": "Get the complete course", "upgrade": "Get Levels 2 to 5"}


class ProductCard(ProductCardTemplate):
    """One offer on the Buy page. item = {product, kind, price, owned, open, currency, course, best, picked}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        kind = it["kind"]
        self.title.text = i18n.t(TITLES[kind])
        self.price.text = shop.money(it, it["price"])
        self.price_note.text = i18n.t("one time, yours to keep")
        for k, box in (("level1", self.list_level1), ("complete", self.list_complete), ("upgrade", self.list_upgrade)):
            box.visible = k == kind
        self.buy_button.text = i18n.t(BUTTONS[kind])
        self.buy_button.visible = not it["owned"]
        self.owned_link.visible = bool(it["owned"])
        state.set_attr(self.owned_link, "href", router.href("home", it["course"]))
        if it.get("best") and not it["owned"]:
            self.tag.text, self.tag.visible = i18n.t("Best value"), True
        if it.get("picked"):
            self.tag.text, self.tag.visible = i18n.t("You picked this one"), True
        self.card.classes["sb-plan-best"] = bool(it.get("best") or it.get("picked"))
        self.card.classes["sb-plan-owned"] = bool(it["owned"])
        state.set_attr(self.buy_button, "data-product", it["product"])
        i18n.apply(anvil.js.get_dom_node(self))

    @handle("buy_button", "click")
    def buy_button_click(self, **event_args):
        shop.buy(self.item["product"])
