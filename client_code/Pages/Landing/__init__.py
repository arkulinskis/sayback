from anvil import *
import anvil.js

from ._anvil_designer import LandingTemplate
from ... import shop, state

COURSE = "en-es"


class Landing(LandingTemplate):
    """#landing: the sales page for English speakers (Sayback Spanish). Persuade mode: the live road demo, the
    stolen-minutes promise, the method, the three beliefs, the offer and the guarantee. Static copy lives in the
    template; prices come from Admin -> Shop (shop_info), so they're never out of date.
    The Spanish twin is Pages/LandingEs."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        if me:
            state.set_attr(self.band_link, "href", "#home")
            anvil.js.get_dom_node(self.band_link).textContent = "Open your library"
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
        shop.buy("es1")

    @handle("buy_complete", "click")
    def buy_complete_click(self, **event_args):
        shop.buy("esall")

    def leave(self):
        self.road.stop()
