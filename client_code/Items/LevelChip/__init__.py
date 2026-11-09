from anvil import *

from ._anvil_designer import LevelChipTemplate
from ... import i18n, router, state


class LevelChip(LevelChipTemplate):
    """A level in the library's level picker: name, lessons done, a lock if not owned. A link (#home/course/level),
    so the browser's back button works. item = {level, name {en, es}, done, count, owned, on, course}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        state.set_attr(self, "href", router.href("home", it["course"], it["level"]))
        if it.get("on"):
            state.set_attr(self, "aria-current", "true")
        self.label.text = i18n.t("Level {n}").replace("{n}", str(it["level"]))
        self.name.text = i18n.pick(it["name"])
        self.count.text = "%d / %d" % (it["done"], it["count"])
        self.lock.visible = not it["owned"]
        self.meter.style["transform"] = "scaleX(%.3f)" % (it["done"] / float(it["count"] or 1))
        self.classes["on"] = bool(it.get("on"))
        self.classes["locked"] = not it["owned"]
