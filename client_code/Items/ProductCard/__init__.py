from anvil import *
import anvil.js

from ._anvil_designer import ProductCardTemplate
from ... import i18n, router, shop, state

TITLES = {"level": "Level {n} · 30 lessons", "complete": "Complete course · Levels 1 to 5",
          "upgrade": "Upgrade · Levels 2 to 5", "bundle": "Every language · Spanish, French, Italian"}
BUTTONS = {"level": "Get Level {n}", "complete": "Get the complete course", "upgrade": "Get Levels 2 to 5",
           "bundle": "Get every language"}
GIFT_BUTTONS = {"level": "Give Level {n}", "complete": "Give the complete course", "bundle": "Give every language"}


class ProductCard(ProductCardTemplate):
    """One offer on the Buy page (and, with item["gift"], on the gift page).
    item = {product, kind, price, owned, open, currency, course, best, picked, gift?}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        kind = it["kind"]
        n = str(it.get("level") or 1)
        free = not it.get("gift") and it["price"] is not None and float(it["price"]) <= 0
        self.title.text = i18n.t(TITLES[kind]).replace("{n}", n)
        if kind == "complete" and it.get("credit") and not it["owned"]:
            self.title.text = i18n.t("The rest of the course · {count} levels").replace("{count}", str(len(it.get("levels") or [])))
        self.price.text = i18n.t("Free") if free else shop.money(it, it["price"])
        self.price_note.text = (i18n.t("your levels already add up to the course price") if free else
                                i18n.t("the levels you own count toward it") if it.get("credit") else
                                i18n.t("one time, lifetime access"))
        for k, box in (("level", self.list_level1), ("complete", self.list_complete), ("upgrade", self.list_upgrade),
                       ("bundle", self.list_bundle)):
            box.visible = k == kind
        self.buy_button.text = (i18n.t("Unlock Level {n} free") if free else
                                i18n.t(GIFT_BUTTONS[kind] if it.get("gift") else BUTTONS[kind])).replace("{n}", n)
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
        shop.buy(self.item["product"], gift=bool(self.item.get("gift")))
