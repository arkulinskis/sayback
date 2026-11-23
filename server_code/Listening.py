"""The member side: the library (levels, lessons, what's next), one lesson (audio link, phrase sheet, culture note),
saved positions, and the listening stats (stolen minutes this week, streak).

Streak: a day counts at 60 s of listening; one missed day per rolling 7 days is a rest day (the streak stays, it
just doesn't grow). Weekly goal: listener_prefs.goal_minutes (45/90/150/225, default 90), read in try/except so the
library works before the user accepts the new table.

Dates: the browser sends its own date ("today", YYYY-MM-DD) so a streak follows the person's day, not UTC.
"""
import datetime as dt

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Audio, Catalog, DemoData, Shop
from . import courses as K

LESSON_SECONDS = 2700
DONE_AT = 0.93          # 93% heard = done (the outro and the fade-out don't have to be sat through)
GOALS = (45, 90, 150, 225)
DEFAULT_GOAL = 90
DAY_SECONDS = 60        # a day counts for the streak once you've listened this long
REST_EVERY = 7          # one missed day per this many days is forgiven


def _day(today):
    """The browser's date if it's within a day of the server's, else the server's (UTC)."""
    server = C.now().date()
    try:
        d = dt.date.fromisoformat(str(today)[:10])
    except ValueError:
        return server
    return d if abs((d - server).days) <= 1 else server


def _course_for(me, course, fallback=None):
    """The asked-for course, else one the person owns, else the fallback (the page language's course)."""
    if Catalog.course_ok(course):
        return course
    owned = Catalog.live_purchases(me)
    if owned:
        return owned[0]["course"]
    return fallback if Catalog.course_ok(fallback) else "en-es"


def _progress(me, course):
    return {r["code"]: r for r in app_tables.progress.search(user=me, course=course)}


def stats(me, course, today):
    day = _day(today)
    rows = list(app_tables.listening.search(user=me, course=course))
    by_day: dict = {}
    for r in rows:
        if r["day"] is not None:
            by_day[r["day"]] = by_day.get(r["day"], 0) + (r["seconds"] or 0)
    week = sum(v for d, v in by_day.items() if 0 <= (day - d).days < 7)
    streak, rest_used = streak_of(by_day, day)
    last14 = [{"day": (day - dt.timedelta(days=13 - i)).isoformat(),
               "minutes": int(by_day.get(day - dt.timedelta(days=13 - i), 0) // 60)} for i in range(14)]
    return {"week_minutes": int(week // 60), "total_minutes": int(sum(by_day.values()) // 60), "streak": streak,
            "rest_used": rest_used, "goal": goal_of(me), "days": last14, "today_minutes": int(by_day.get(day, 0) // 60)}


def streak_of(by_day, day):
    """(streak, rest_used). Walks back from today (or yesterday, if today has under a minute so far). A missed day is
    forgiven when the day before it was listened to and no other forgiven day is within REST_EVERY days of it; rest
    days keep the streak but don't add to it. rest_used = a forgiven day in the last 7 days."""
    one = dt.timedelta(days=1)

    def heard(x):
        return by_day.get(x, 0) >= DAY_SECONDS

    d = day if heard(day) else day - one   # today not started yet: the streak still counts up to yesterday
    oldest = min(by_day) if by_day else day
    streak, forgiven = 0, []
    while d >= oldest:
        if heard(d):
            streak += 1
        elif heard(d - one) and (not forgiven or (forgiven[-1] - d).days >= REST_EVERY):
            forgiven.append(d)             # a rest day: the streak carries on behind it
        else:
            break
        d -= one
    if not streak:
        return 0, False
    return streak, any((day - f).days < 7 for f in forgiven)


def goal_of(me):
    """The person's weekly goal in minutes (default 90). Safe before the listener_prefs table exists."""
    try:
        r = app_tables.listener_prefs.get(user=me)
        g = int(r["goal_minutes"] or 0) if r is not None else 0
        return g if g in GOALS else 0
    except Exception:
        return 0   # 0 = not chosen (or not saved yet): the browser's choice or the default applies


def part_of(pos, marks):
    """Which third of the lesson a saved position is in (1-3); the pep talks at marks[1] and marks[2] start parts 2, 3."""
    if not marks or len(marks) < 3:
        return 1
    return 1 + int(pos >= marks[1] - 3) + int(pos >= marks[2] - 3)


def _tile(ls, prog, me, course):
    r = prog.get(ls["code"])
    locked = not Catalog.can_play(me, course, ls["code"])
    pos = (r["position"] or 0) if r is not None else 0
    done = bool(r is not None and r["done"])
    state = "locked" if locked else ("done" if done else ("started" if pos > 20 else "open"))
    return {"code": ls["code"], "n": ls["n"], "level": ls["level"], "title": ls["title"], "state": state,
            "free": Catalog.is_free(ls["code"]), "pct": min(100, int(pos * 100 / LESSON_SECONDS)) if pos else 0,
            "part": part_of(pos, ls.get("marks")) if state == "started" else 1, "course": course}


def next_lesson(me, course, prog):
    """The lesson to press play on: a started one (most recent), else the first one not done yet."""
    started = [r for r in prog.values() if not r["done"] and (r["position"] or 0) > 20]
    if started:
        r = max(started, key=lambda x: x["updated"] or C.now())
        ls = Catalog.lesson(course, r["code"])
        if ls is not None:
            return ls, r["position"] or 0
    for ls in Catalog.lessons(course):
        r = prog.get(ls["code"])
        if r is None or not r["done"]:
            return ls, 0
    return None, 0


@anvil.server.callable(require_user=True)
def library(course=None, level=None, today="", fallback=None):
    """Everything the library page shows, in one call."""
    me = C.require_user()
    DemoData.ensure_loaded()
    course = _course_for(me, course, fallback)
    prog = _progress(me, course)
    owned = Catalog.owned_levels(me, course)
    levels = []
    for lv in Catalog.LEVELS:
        lessons = [ls for ls in Catalog.lessons(course) if ls["level"] == lv]
        done = len([1 for ls in lessons if prog.get(ls["code"]) is not None and prog[ls["code"]]["done"]])
        levels.append({"level": lv, "name": {"en": Catalog.level_name(lv, "en"), "es": Catalog.level_name(lv, "es")},
                       "done": done, "count": len(lessons), "owned": lv in owned or C.is_admin(me)})
    nxt, pos = next_lesson(me, course, prog)
    if level not in Catalog.LEVELS:
        level = nxt["level"] if nxt else 1
    tiles = [_tile(ls, prog, me, course) for ls in Catalog.lessons(course) if ls["level"] == level]
    nd = None
    if nxt is not None:
        nd = {"code": nxt["code"], "level": nxt["level"], "n": nxt["n"], "title": nxt["title"],
              "situation": nxt["situation"], "position": int(pos),
              "part": part_of(pos, nxt.get("marks")) if pos > 20 else 1, "marks": nxt.get("marks"),
              "locked": not Catalog.can_play(me, course, nxt["code"])}
    return {"course": course, "name": Catalog.course_name(course), "level": level, "levels": levels, "lessons": tiles,
            "next": nd, "stats": stats(me, course, today), "owned": sorted(owned), "is_admin": C.is_admin(me),
            "courses": [{"course": c, "lang": K.COURSES[c]["lang"], "learner": K.COURSES[c]["learner"],
                         "owned": bool(Catalog.owned_levels(me, c))} for c in Catalog.COURSES],
            "done_total": len([1 for r in prog.values() if r["done"]]),
            "shop": Shop.shop_public(course, me), "audio": Audio.status() != "none"}


@anvil.server.callable(require_user=True)
def get_lesson(course, code):
    me = C.require_user()
    ls = Catalog.lesson(course, code)
    if ls is None:
        return C.fail("That lesson doesn't exist.")
    why = Catalog.why_locked(me, course, code)
    r = app_tables.progress.get(user=me, course=course, code=code)
    prev, nxt = Catalog.neighbours(course, code)
    url = download = transcript = None
    cues = ""
    if not why:
        url = Audio.url_for(ls["file"])
        download = Audio.url_for(ls["file"], ls["download"])
        transcript = Audio.url_for(ls["file"][:-4] + ".txt", ls["download"][:-4] + ".txt")
        cues = lesson_cues(course, code)   # only for lessons the person may hear
    updated = r["updated"] if r is not None else None
    def brief(c):
        x = Catalog.lesson(course, c) if c else None
        return {"code": x["code"], "title": x["title"], "locked": not Catalog.can_play(me, course, x["code"])} if x else None
    return C.ok(course=course, name=Catalog.course_name(course), code=code, level=ls["level"], n=ls["n"],
                level_name={"en": Catalog.level_name(ls["level"], "en"), "es": Catalog.level_name(ls["level"], "es")},
                title=ls["title"], situation=ls["situation"], emotion=ls["emotion"], culture=ls["culture"],
                marks=ls["marks"], locked=why, free=Catalog.is_free(code),
                pairs=ls["pairs"] if not why else ls["pairs"][:3], pair_count=len(ls["pairs"]),
                url=url, download=download, transcript=transcript, audio=Audio.status() != "none",
                position=int((r["position"] or 0) if r is not None else 0), done=bool(r is not None and r["done"]),
                updated=int(updated.timestamp() * 1000) if updated is not None else 0, cues=cues,
                prev=brief(prev), next=brief(nxt), shop=Shop.shop_public(course, me) if why else None)


def lesson_cues(course, code):
    """The thinking-time cues of a lesson (tools/make_catalog.py -> cues_data.py, imported on first use)."""
    try:
        from . import cues_data
        return cues_data.DATA.get(course, {}).get(code, "")
    except Exception:
        return ""


@anvil.server.callable(require_user=True)
def set_goal(minutes):
    """The weekly goal in minutes: only the offered values, saved per account in listener_prefs."""
    me = C.require_user()
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return C.fail("Pick one of the goals.")
    if minutes not in GOALS:
        return C.fail("Pick one of the goals.")
    try:
        r = app_tables.listener_prefs.get(user=me)
        if r is None:
            app_tables.listener_prefs.add_row(user=me, goal_minutes=minutes, updated=C.now(), is_demo=False)
        else:
            r.update(goal_minutes=minutes, updated=C.now())
    except Exception:
        return C.ok(goal=minutes, saved=False)   # table not accepted yet: the browser keeps the choice meanwhile
    return C.ok(goal=minutes, saved=True)


@anvil.server.callable(require_user=True)
def save_progress(course, code, position, listened=0, done=False, today="", queued=False):
    """Called by the player every ~20 s while it plays, on pause and at the end. listened = seconds actually heard
    since the last call (capped, so a stuck browser can't inflate the stats). queued = it also carries seconds from
    saves that failed earlier (a tunnel, a dead zone), so the cap is bigger."""
    me = C.require_user()
    if not Catalog.can_play(me, course, code):
        return C.fail("This lesson is locked.")
    try:
        position = max(0.0, min(float(position or 0), LESSON_SECONDS))
        listened = max(0.0, min(float(listened or 0), 600.0 if queued else 120.0))
    except (TypeError, ValueError):
        return C.fail("Bad position.")
    finished = bool(done) or position >= LESSON_SECONDS * DONE_AT
    r = app_tables.progress.get(user=me, course=course, code=code)
    if r is None:
        r = app_tables.progress.add_row(user=me, course=course, code=code, position=0, done=False, completions=0,
                                        updated=C.now(), is_demo=False)
    newly = finished and not r["done"]
    # a finish counts once: the saves after it (the outro still playing) find the position already back at 0
    counts = finished and (newly or (r["position"] or 0) > 0)
    r.update(position=0 if finished else position, done=bool(r["done"]) or finished, updated=C.now(),
             completions=(r["completions"] or 0) + (1 if counts else 0))
    if listened:
        day = _day(today)
        row = app_tables.listening.get(user=me, course=course, day=day)
        if row is None:
            app_tables.listening.add_row(user=me, course=course, day=day, seconds=listened, is_demo=False)
        else:
            row["seconds"] = (row["seconds"] or 0) + listened
    return C.ok(done=bool(r["done"]), newly_done=newly)


@anvil.server.callable(require_user=True)
def set_done(course, code, flag):
    me = C.require_user()
    if not Catalog.can_play(me, course, code):
        return C.fail("This lesson is locked.")
    r = app_tables.progress.get(user=me, course=course, code=code)
    if r is None:
        r = app_tables.progress.add_row(user=me, course=course, code=code, position=0, done=False, completions=0,
                                        updated=C.now(), is_demo=False)
    r.update(done=bool(flag), position=0, updated=C.now())
    return C.ok(done=bool(flag))


def overview():
    """Admin numbers: people who listened this week, minutes, lessons finished."""
    week_ago = C.now().date() - dt.timedelta(days=7)
    rows = [r for r in app_tables.listening.search() if r["day"] is not None and r["day"] > week_ago]
    return {"listeners_week": len({r["user"].get_id() for r in rows if r["user"] is not None}),
            "minutes_week": int(sum((r["seconds"] or 0) for r in rows) // 60),
            "lessons_done": len(app_tables.progress.search(done=True))}


# ------------------------------------------------------------------------------------------------ offline + downloads
@anvil.server.callable(require_user=True)
def downloads_info(course=None):
    """The Downloads page: the course's five levels, each lesson with its size and whether it may be saved."""
    me = C.require_user()
    course = _course_for(me, course, "en-es")
    levels = []
    for lv in Catalog.LEVELS:
        items = []
        for ls in Catalog.lessons(course):
            if ls["level"] != lv:
                continue
            items.append({"code": ls["code"], "n": ls["n"], "title": ls["title"], "mb": ls.get("mb") or 21.6,
                          "open": Catalog.can_play(me, course, ls["code"])})
        levels.append({"level": lv, "name": {"en": Catalog.level_name(lv, "en"), "es": Catalog.level_name(lv, "es")},
                       "lessons": items, "mb": round(sum(x["mb"] for x in items)),
                       "open": all(x["open"] for x in items)})
    return {"course": course, "name": Catalog.course_name(course), "levels": levels, "audio": Audio.status() != "none",
            "courses": [{"course": c, "lang": K.COURSES[c]["lang"], "owned": bool(Catalog.owned_levels(me, c))}
                        for c in Catalog.COURSES]}


def offline_meta(me, course, ls):
    """What Pages/Lesson needs to show a saved lesson with no connection (no links, no shop)."""
    prev, nxt = Catalog.neighbours(course, ls["code"])
    return {"course": course, "name": Catalog.course_name(course), "code": ls["code"], "level": ls["level"], "n": ls["n"],
            "level_name": {"en": Catalog.level_name(ls["level"], "en"), "es": Catalog.level_name(ls["level"], "es")},
            "title": ls["title"], "situation": ls["situation"], "emotion": ls["emotion"], "culture": ls["culture"],
            "marks": ls["marks"], "pairs": ls["pairs"], "pair_count": len(ls["pairs"]), "cues": lesson_cues(course, ls["code"]),
            "prev": {"code": prev} if prev else None, "next": {"code": nxt} if nxt else None}


@anvil.server.callable(require_user=True)
def offline_pack(course, codes, files=False):
    """Signed links (6 hours) for lessons the person may hear: to save in the browser (with the lesson's details for
    offline play), or with files=True as MP3 downloads. Locked lessons are left out. At most one level per call."""
    me = C.require_user()
    if not Catalog.course_ok(course) or not isinstance(codes, list):
        return C.fail("Pick lessons to save.")
    if C.rate_limited("offline_pack", 40, 3600):
        return C.fail("That's a lot of downloads at once. Please try again in a while.")
    out = []
    for code in codes[:30]:
        ls = Catalog.lesson(course, str(code))
        if ls is None or not Catalog.can_play(me, course, ls["code"]):
            continue
        url = Audio.url_for(ls["file"], ls["download"]) if files else Audio.url_for(ls["file"])
        if not url:
            return C.fail("Lesson audio isn't connected yet.")
        item = {"course": course, "code": ls["code"], "url": url, "mb": ls.get("mb") or 21.6}
        if not files:
            item["meta"] = offline_meta(me, course, ls)
        out.append(item)
    return C.ok(items=out)
