from anvil import *
from anvil.js import window

from ._anvil_designer import LibraryTemplate
from ... import i18n, router, state


def today():
    """The browser's own date (YYYY-MM-DD), so streaks follow the listener's day."""
    return str(window.Date().toLocaleDateString("en-CA"))[:10]


def fmt(sec):
    sec = int(sec or 0)
    return "%d:%02d" % (sec // 60, sec % 60)


class Library(LibraryTemplate):
    """#home[/course[/level]]: the member's library. Up next (play / resume / car mode), the stolen-minutes stats with
    a 14-day chart, the five levels, the 30 lessons of the chosen level, and the offers for what isn't owned yet.
    One server call (library)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        course = args[0] if args else state.store_get("sayback.course")
        level = int(args[1]) if len(args) > 1 and str(args[1]).isdigit() else None
        d = state.call("library", course, level, today(), "es-en" if i18n.lang() == "es" else "en-es")
        self.d = d
        state.store_set("sayback.course", d["course"])
        self._head(d)
        self._next(d)
        self._stats(d)
        self._levels(d)
        state.heading(self.hello, 1)

    def _head(self, d):
        me = state.me() or {}
        first = (me.get("name") or "").split(" ")[0]
        hour = window.Date().getHours()
        greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        self.hello.text = (i18n.t(greet) + (", " + first if first else "")).strip()
        self.course_line.text = "%s · %s" % (d["name"], i18n.t("{n} of 150 lessons done").replace("{n}", str(d["done_total"])))
        self.sw_es.classes["on"] = d["course"] == "en-es"
        self.sw_en.classes["on"] = d["course"] == "es-en"
        if not d["audio"] and d["is_admin"]:
            self.audio_warn.text = ("Lesson audio isn't connected yet, so lessons can't play. Admin > Shop & setup "
                                    "shows the two steps (upload to Cloudflare R2, then the r2_url App Secret).")
            self.audio_warn.visible = True

    def _next(self, d):
        n = d["next"]
        self.next_card.visible = bool(n) and not n["locked"]
        self.unlock_card.visible = bool(n) and n["locked"]
        self.finished_card.visible = not n
        if not n:
            return
        title = i18n.pick(n["title"])
        meta = "%s · %s · %s" % (i18n.t("Level {n}").replace("{n}", str(n["level"])),
                                 i18n.t("Lesson {n}").replace("{n}", str(n["n"])), i18n.pick(n["situation"]))
        if n["locked"]:
            self.unlock_title.text = i18n.t("You've heard the free lesson. Ready for the rest?")
            self.unlock_text.text = i18n.t("Next up: {title}. Unlock Level 1 to keep going tomorrow morning.").replace("{title}", title)
            state.set_attr(self.unlock_link, "href", router.href("buy", d["course"]))
            return
        self.next_title.text = title
        self.next_meta.text = meta
        pos = n["position"]
        self.next_bar.visible = pos > 20
        self.next_fill.style["transform"] = "scaleX(%.3f)" % min(1.0, pos / 2700.0)
        self.play_button.text = i18n.t("Resume at {t}").replace("{t}", fmt(pos)) if pos > 20 else i18n.t("Play lesson")
        self.car_button.text = i18n.t("Car mode")

    def _stats(self, d):
        s = d["stats"]
        self.week_min.text = str(s["week_minutes"])
        self.streak.text = str(s["streak"])
        self.done_count.text = str(d["done_total"])
        top = max([x["minutes"] for x in s["days"]] + [1])
        days = s["days"]
        self.bars.items = [dict(x, max=top, today=(i == len(days) - 1)) for i, x in enumerate(days)]

    def _levels(self, d):
        lv = d["level"]
        self.levels_panel.items = [dict(x, course=d["course"], on=x["level"] == lv) for x in d["levels"]]
        info = [x for x in d["levels"] if x["level"] == lv][0]
        self.level_title.text = "%s · %s" % (i18n.t("Level {n}").replace("{n}", str(lv)), i18n.pick(info["name"]))
        if info["owned"]:
            self.level_note.text = i18n.t("{done} of {count} done").replace("{done}", str(info["done"])).replace("{count}", str(info["count"]))
        elif lv == 1:
            self.level_note.text = i18n.t("Lesson 1 is free. Unlock Level 1 for the other 29.")
        else:
            self.level_note.text = i18n.t("Locked. Lesson titles are here so you can see what's coming.")
        self.lessons_panel.items = d["lessons"]
        shop = d["shop"]
        offers = [dict(p, currency=shop["currency"], course=d["course"], best=p["kind"] in ("complete", "upgrade"))
                  for p in shop["products"] if not p["owned"]]
        self.offers.items = offers
        self.offer_part.visible = bool(offers)

    @handle("play_button", "click")
    def play_button_click(self, **event_args):
        n = self.d["next"]
        router.go("lesson", self.d["course"], n["code"], "play")

    @handle("car_button", "click")
    def car_button_click(self, **event_args):
        n = self.d["next"]
        router.go("lesson", self.d["course"], n["code"], "car")
