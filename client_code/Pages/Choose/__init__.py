from anvil import *
import anvil.js

from ._anvil_designer import ChooseTemplate
from ... import i18n, state


class Choose(ChooseTemplate):
    """#landing: the front door. "I speak English / Español" + "I want to learn ..." send people to a course's sales
    page (#learn/<slug> or #es). Below: why speaking beats tapping, the car promise, the gift band, a short FAQ.
    Ads link straight to the course pages, so this page is for people who arrive with no language in mind."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        if me:
            state.set_attr(self.band_link, "href", "#home")
            anvil.js.get_dom_node(self.band_link).textContent = "Open your library"
        self._speak("es" if i18n.lang() == "es" or state.store_get("sm.speak") == "es" else "en")

    def _speak(self, lang):
        self.speak_en.classes["on"] = lang == "en"
        self.speak_es.classes["on"] = lang == "es"
        self.learn_en.visible = lang == "en"
        self.learn_es.visible = lang == "es"
        anvil.js.get_dom_node(self.learn_label).textContent = "Quiero aprender" if lang == "es" else "I want to learn"
        state.set_attr(self.learn_label, "lang", lang)

    def speak_click(self, event):
        lang = event.currentTarget.getAttribute("data-speak") or "en"
        state.store_set("sm.speak", lang)
        self._speak(lang)

    def leave(self):
        self.road.stop()
