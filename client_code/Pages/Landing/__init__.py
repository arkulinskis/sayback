from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import LandingTemplate
from ... import courses, router, shop, state

# Words that change per language: <span data-v="key"> in the template (the template itself shows the Spanish ones).
VALUES: dict = {
    "en-es": {
        "lang": "Spanish", "city": "Madrid",
        "level5": "Mexico, Spain, Argentina and Colombia in Level 5",
        "variant": "Clear, neutral Spanish understood everywhere, using “ustedes” rather than Spain-only “vosotros”. "
                   "The culture notes cover Spain, Mexico and South America, and Level 5 adds regional flavour.",
        "voices": "Natural-sounding AI voices: a woman and a man, so you hear how phrases change with who is speaking "
                  "(“cansado”, “cansada”). That's also how we keep the price this low.",
    },
    "en-fr": {
        "lang": "French", "city": "Paris",
        "level5": "Paris, Montréal, Belgium, Senegal and Martinique in Level 5",
        "variant": "Standard French as spoken in France, understood everywhere from Montréal to Dakar. The culture "
                   "notes cover France, Belgium, Switzerland, Québec and West Africa, and Level 5 adds regional flavour.",
        "voices": "Natural-sounding AI voices: one clear French voice for the answers and an English voice for the "
                  "prompts, so every phrase sounds the same each time you hear it. That's also how we keep the price this low.",
    },
    "en-it": {
        "lang": "Italian", "city": "Rome",
        "level5": "Rome, Milan, Naples and Sicily in Level 5",
        "variant": "Standard Italian, the Italian of TV, newspapers and everyday life across Italy. The culture notes "
                   "travel from Milan to Sicily, and Level 5 adds regional flavour.",
        "voices": "Natural-sounding AI voices: a woman and a man, so you hear how phrases change with who is speaking "
                  "(“stanco”, “stanca”). That's also how we keep the price this low.",
    },
}


# The app's video on the Addanapp YouTube channel (APP_MAKER/youtube/manifest.json), shown in the Watch section.
YT_VIDEO = "xlkFBbenusw"


class Landing(LandingTemplate):
    """#learn/<spanish|french|italian>: the sales page for English speakers, one template for the three languages
    (VALUES fills the <span data-v> words). Persuade mode: the live road demo, the car promise, the method, speaking vs
    tapping, the beliefs, offline, the offer (Level 1, complete, every language), gifts, the guarantee, FAQ.
    Prices come from Admin -> Shop (shop_info). Ads link straight here (client_code/ads.py keeps the UTM tags)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.dom_nodes["yt_cover"].addEventListener("click", self._play)
        self.course = courses.by_slug(args[0] if args else "") or "en-es"
        if self.course not in VALUES:
            self.course = "en-es"
        c = courses.COURSES[self.course]
        v = VALUES[self.course]
        node = anvil.js.get_dom_node(self)
        for el in window.Array["from"](node.querySelectorAll("[data-v]")):
            key = el.getAttribute("data-v")
            if key in v:
                el.textContent = v[key]
        sample = anvil.js.get_dom_node(self.sample_a)
        sample.textContent = "“%s”" % c["sample"][1]
        sample.setAttribute("lang", str(c["target"]))
        self.road.course = self.course
        for code, el in (("en-es", self.sw_es), ("en-fr", self.sw_fr), ("en-it", self.sw_it)):
            el.classes["on"] = code == self.course
            state.set_attr(el, "aria-current", "page" if code == self.course else None)
        self.bridge.visible = self.course == "en-es"
        state.set_attr(self.gift_link, "href", router.href("gift", self.course))
        window.document.title = "Speak %s on your drive · Spoken Miles" % v["lang"]
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        if me:
            state.set_attr(self.member_lib, "href", router.href("home", self.course))
            state.set_attr(self.member_buy, "href", router.href("buy", self.course))
            state.set_attr(self.band_link, "href", "#home")
            anvil.js.get_dom_node(self.band_link).textContent = "Open your library"
        self._fill()

    def _play(self, event):
        """Swap the video's cover for YouTube's player (privacy-enhanced); nothing loads from YouTube before this click."""
        self.dom_nodes["yt_frame"].innerHTML = (
            '<iframe src="https://www.youtube-nocookie.com/embed/' + YT_VIDEO + '?autoplay=1&rel=0&playsinline=1" '
            'title="Spoken Miles video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe>')

    def _fill(self):
        s = shop.info(self.course)
        if not s:
            return
        prices = {p["kind"]: p["price"] for p in s["products"]}
        for g in s.get("gifts") or []:
            prices.setdefault(g["kind"], g["price"])
        if "level1" in prices:
            self.price_level1.text = shop.money(s, prices["level1"])
        if "complete" in prices:
            self.price_complete.text = shop.money(s, prices["complete"])
        if "bundle" in prices:
            self.price_bundle.text = shop.money(s, prices["bundle"])
        self.guarantee_days.text = str(s.get("guarantee_days") or 30)

    @handle("buy_level1", "click")
    def buy_level1_click(self, **event_args):
        shop.buy(courses.product_for(self.course, "level1"))

    @handle("buy_complete", "click")
    def buy_complete_click(self, **event_args):
        shop.buy(courses.product_for(self.course, "complete"))

    @handle("buy_bundle", "click")
    def buy_bundle_click(self, **event_args):
        shop.buy("trio")

    def leave(self):
        self.road.stop()
