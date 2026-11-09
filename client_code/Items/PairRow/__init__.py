from anvil import *
import anvil.js

from ._anvil_designer import PairRowTemplate
from ... import i18n, state


class PairRow(PairRowTemplate):
    """One phrase on a lesson's phrase sheet: prompt, answer, and who says it when the answer changes with the
    speaker (cansado / cansada). In quiz mode the answer stays hidden until the row is tapped.
    item = {i, p, a, g, hide, lang}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        anvil.js.get_dom_node(self.n_box).textContent = str(it["i"])
        self.who.text = {"f": i18n.t("a woman says"), "m": i18n.t("a man says")}.get(it.get("g") or "", "")
        self.who.visible = bool(it.get("g"))
        state.set_attr(self.answer, "lang", it.get("lang") or None)
        self.shown = not it.get("hide")
        self._draw()

    def _draw(self):
        self.btn.classes["hidden-answer"] = not self.shown
        el = anvil.js.get_dom_node(self.btn)
        el.setAttribute("aria-expanded", "true" if self.shown else "false")
        el.setAttribute("aria-label", self.item["p"] + (" → " + self.item["a"] if self.shown else " · " + i18n.t("tap to show the answer")))

    def btn_click(self, event):
        self.shown = not self.shown
        self._draw()
