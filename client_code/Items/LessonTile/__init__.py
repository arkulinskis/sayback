from anvil import *

from ._anvil_designer import LessonTileTemplate
from ... import i18n, router, state

ICONS = {"done": "ic-check", "locked": "ic-lock", "started": "ic-play", "open": "ic-play"}


class LessonTile(LessonTileTemplate):
    """One lesson in the library grid. item = {code, n, level, title {en, es}, state, free, pct, course}.
    state: done / started (pct heard) / open / locked. The whole tile is a link to the lesson."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        st = it["state"]
        state.set_attr(self, "href", router.href("lesson", it["course"], it["code"]))
        state.set_attr(self, "data-key", it["code"])
        self.title.text = i18n.pick(it["title"])
        if st == "done":
            self.status.text = i18n.t("Done")
        elif st == "started":
            self.status.text = i18n.t("{pct}% heard").replace("{pct}", str(it["pct"]))
        elif st == "locked":
            self.status.text = i18n.t("Locked")
        else:
            self.status.text = i18n.t("Free") if it.get("free") else i18n.t("Ready")
        self.classes.add("st-" + st)
        self.icon.classes.add(ICONS.get(st, "ic-play"))
        self.bar.visible = st == "started"
        self.bar_fill.style["transform"] = "scaleX(%.3f)" % (min(100, it["pct"]) / 100.0)
