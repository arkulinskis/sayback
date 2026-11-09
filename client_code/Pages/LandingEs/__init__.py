from anvil import *
import anvil.js

from ._anvil_designer import LandingEsTemplate
from ... import shop, state

COURSE = "es-en"


class LandingEs(LandingEsTemplate):
    """#es: la página de ventas para hispanohablantes (Sayback Inglés). The Spanish twin of Pages/Landing: same
    sections, written in Spanish (not translated on the fly), course es-en, products en1 / enall."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        if me:
            state.set_attr(self.band_link, "href", "#home")
            anvil.js.get_dom_node(self.band_link).textContent = "Abre tu biblioteca"
        self._fill()

    def _fill(self):
        s = shop.info(COURSE)
        if not s:
            return
        prices = {p["kind"]: p["price"] for p in s["products"]}
        if "level1" in prices:
            self.price_level1.text = shop.money(s, prices["level1"])
        if "complete" in prices:
            self.price_complete.text = shop.money(s, prices["complete"])
        self.guarantee_days.text = str(s.get("guarantee_days") or 30)

    @handle("buy_level1", "click")
    def buy_level1_click(self, **event_args):
        shop.buy("en1")

    @handle("buy_complete", "click")
    def buy_complete_click(self, **event_args):
        shop.buy("enall")

    def leave(self):
        self.road.stop()
