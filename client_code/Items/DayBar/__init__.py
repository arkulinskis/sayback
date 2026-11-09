from anvil import *

from ._anvil_designer import DayBarTemplate
from ... import i18n, state

DAYS = {"en": "MTWTFSS", "es": "LMXJVSD"}


class DayBar(DayBarTemplate):
    """One day in the library's 14-day chart. item = {day (YYYY-MM-DD), minutes, max, today}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        y, m, d = [int(x) for x in it["day"].split("-")]
        import datetime
        wd = datetime.date(y, m, d).weekday()
        self.day.text = DAYS[i18n.lang()][wd]
        top = max(it.get("max") or 0, 45)
        self.fill.style["transform"] = "scaleY(%.3f)" % min(1.0, it["minutes"] / float(top))
        self.classes["today"] = bool(it.get("today"))
        self.classes["zero"] = it["minutes"] == 0
        state.set_attr(self, "title", "%s: %d min" % (it["day"], it["minutes"]))
