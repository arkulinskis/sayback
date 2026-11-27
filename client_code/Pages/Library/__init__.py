from anvil import *
import anvil.server
from anvil.js import window

from ._anvil_designer import LibraryTemplate
from ... import i18n, router, state


def today():
    """The browser's own date (YYYY-MM-DD), so streaks follow the listener's day."""
    return str(window.Date().toLocaleDateString("en-CA"))[:10]


def fmt(sec):
    sec = int(sec or 0)
    return "%d:%02d" % (sec // 60, sec % 60)


GOALS = (45, 90, 150, 225)
DEFAULT_GOAL = 90
TRIPS = (15, 30, 0)


def stored_int(key, allowed, default):
    try:
        v = int(state.store_get(key, default) or 0)
    except (TypeError, ValueError):
        v = default
    return v if v in allowed else default


class Library(LibraryTemplate):
    """#home[/course[/level]]: the member's library. Up next (play / resume / car mode, trip length), the weekly goal
    ring (stolen minutes this week of 45/90/150/225), the streak with its weekly rest day, a 14-day chart, the five
    levels, the 30 lessons of the chosen level, and the offers for what isn't owned yet. One server call (library)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        if state.OFFLINE["on"]:
            router.go("downloads")          # no connection: the saved lessons are on the Offline page
            return
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
        for code, el in (("en-es", self.sw_es), ("en-fr", self.sw_fr), ("en-it", self.sw_it), ("es-en", self.sw_en)):
            el.classes["on"] = code == d["course"]
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
        if n["position"] > 20 and n.get("part", 1) > 1:
            meta += " · " + i18n.t("Part {n} of 3 next").replace("{n}", str(n["part"]))
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
        self._show_trip()

    def _show_trip(self):
        trip = stored_int("sb.trip", TRIPS, 0)
        for v, el in ((15, self.trip_15), (30, self.trip_30), (0, self.trip_0)):
            el.classes["on"] = v == trip

    def trip_click(self, event):
        state.store_set("sb.trip", int(event.currentTarget.getAttribute("data-trip") or 0))
        self._show_trip()

    def _stats(self, d):
        s = d["stats"]
        self.streak.text = str(s["streak"])
        self.today_min.text = str(s.get("today_minutes", 0))
        self.done_count.text = str(d["done_total"])
        if s.get("rest_used"):
            self.rest_note.text = i18n.t("Rest day used: streak safe. Listen tomorrow to keep it going.")
            self.rest_note.role = ["sb-rest-note", "used"]
        else:
            self.rest_note.text = i18n.t("One rest day a week: miss a day and your streak waits for you.")
            self.rest_note.role = ["sb-rest-note"]
        # the account's goal; before it's saved there (or before the new table exists), this browser's choice
        self.goal = s.get("goal") if s.get("goal") in GOALS else stored_int("sb.goal", GOALS, DEFAULT_GOAL)
        self._goal(s["week_minutes"])
        top = max([x["minutes"] for x in s["days"]] + [1])
        days = s["days"]
        self.bars.items = [dict(x, max=top, today=(i == len(days) - 1)) for i, x in enumerate(days)]

    def _goal(self, week):
        goal = self.goal
        self.week_min.text = str(week)
        self.goal_line.text = i18n.t("{n} of {goal} stolen minutes this week").replace("{n}", str(week)).replace("{goal}", str(goal))
        left = goal - week
        if left <= 0:
            self.goal_sub.text = i18n.t("Goal reached. Every minute from here is a bonus.")
        elif week == 0:
            self.goal_sub.text = i18n.t("A fresh week. One trip gets the ring moving.")
        else:
            self.goal_sub.text = i18n.t("{n} minutes to go.").replace("{n}", str(left))
        pct = min(100.0, week * 100.0 / max(1, goal))
        self.dom_nodes["ring_fg"].style.strokeDashoffset = str(round(100 - pct, 2))
        self.dom_nodes["ring_fg"].classList.toggle("full", left <= 0)
        for v, el in ((45, self.goal_45), (90, self.goal_90), (150, self.goal_150), (225, self.goal_225)):
            el.classes["on"] = v == goal

    def goal_click(self, event):
        v = int(event.currentTarget.getAttribute("data-goal") or DEFAULT_GOAL)
        if v not in GOALS:
            return
        self.goal = v
        state.store_set("sb.goal", v)
        self._goal(self.d["stats"]["week_minutes"])
        try:
            r = anvil.server.call_s("set_goal", v)
        except Exception:
            r = None
        if not (isinstance(r, dict) and r.get("ok")):
            state.toast(i18n.t("Your goal is kept on this device for now."), "ok")

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
        offers = [dict(p, currency=shop["currency"], course=d["course"], best=p["kind"] == "complete")
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
