from anvil import *

from ._anvil_designer import BuyTemplate
from ... import courses, i18n, router, shop, state


class Buy(BuyTemplate):
    """#buy/<course>[/<product>]: the offers for one course (the next level, or the one picked, + the rest of the course),
    the guarantee and the checkout facts. A visitor who picked a plan on a sales page comes back here after signing
    up, with that plan marked "You picked this one"."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        default = "es-en" if i18n.lang() == "es" else "en-es"
        self.course = args[0] if args and args[0] in courses.COURSES else default
        picked = args[1] if len(args) > 1 else ""
        s: dict = shop.info(self.course, picked) or {}
        products: list = s.get("products") or []
        self.heading.text = s.get("name") or "Spoken Miles"
        state.heading(self.heading, 1)
        self.sub.text = i18n.t("Pay once. Lifetime access. Listen anywhere, even with no signal.")
        for code, el in (("en-es", self.sw_es), ("en-fr", self.sw_fr), ("en-it", self.sw_it), ("es-en", self.sw_en)):
            el.classes["on"] = code == self.course
        state.set_attr(self.gift_link, "href", router.href("gift", self.course))
        self.offers.items = [dict(p, currency=s.get("currency") or "$", course=self.course,
                                  best=p["kind"] == "complete" and not picked, picked=p["product"] == picked)
                             for p in products]   # a level + the rest of the course + every language (English speakers)
        self.days.text = str(s.get("guarantee_days") or 30)
        closed = bool(products) and not any(p["open"] for p in products if not p["owned"])
        if closed:
            self.closed_note.text = i18n.t("Sales open very soon. The buttons put you on the list for opening day, with an early-listener price.")
            self.closed_note.visible = True
        self.free_part.visible = not state.me()
