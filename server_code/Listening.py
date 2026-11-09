"""The member side: the library (levels, lessons, what's next), one lesson (audio link, phrase sheet, culture note),
saved positions, and the listening stats (stolen minutes this week, streak).

Dates: the browser sends its own date ("today", YYYY-MM-DD) so a streak follows the person's day, not UTC.
"""
import datetime as dt

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Audio, Catalog, DemoData, Shop

LESSON_SECONDS = 2700
DONE_AT = 0.93          # 93% heard = done (the outro and the fade-out don't have to be sat through)


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
    streak, d = 0, day
    if by_day.get(d, 0) < 60:
        d = d - dt.timedelta(days=1)   # today not started yet: the streak still counts up to yesterday
    while by_day.get(d, 0) >= 60:
        streak += 1
        d = d - dt.timedelta(days=1)
    last14 = [{"day": (day - dt.timedelta(days=13 - i)).isoformat(),
               "minutes": int(by_day.get(day - dt.timedelta(days=13 - i), 0) // 60)} for i in range(14)]
    return {"week_minutes": int(week // 60), "total_minutes": int(sum(by_day.values()) // 60), "streak": streak,
            "days": last14, "today_minutes": int(by_day.get(day, 0) // 60)}


def _tile(ls, prog, me, course):
    r = prog.get(ls["code"])
    locked = not Catalog.can_play(me, course, ls["code"])
    pos = (r["position"] or 0) if r is not None else 0
    done = bool(r is not None and r["done"])
    state = "locked" if locked else ("done" if done else ("started" if pos > 20 else "open"))
    return {"code": ls["code"], "n": ls["n"], "level": ls["level"], "title": ls["title"], "state": state,
            "free": Catalog.is_free(ls["code"]), "pct": min(100, int(pos * 100 / LESSON_SECONDS)) if pos else 0,
            "course": course}


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
              "situation": nxt["situation"], "position": int(pos), "locked": not Catalog.can_play(me, course, nxt["code"])}
    return {"course": course, "name": Catalog.course_name(course), "level": level, "levels": levels, "lessons": tiles,
            "next": nd, "stats": stats(me, course, today), "owned": sorted(owned), "is_admin": C.is_admin(me),
            "other": {"en-es": "es-en", "es-en": "en-es"}[course],
            "other_owned": bool(Catalog.owned_levels(me, {"en-es": "es-en", "es-en": "en-es"}[course])),
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
    if not why:
        url = Audio.url_for(ls["file"])
        download = Audio.url_for(ls["file"], ls["download"])
        transcript = Audio.url_for(ls["file"][:-4] + ".txt", ls["download"][:-4] + ".txt")
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
                prev=brief(prev), next=brief(nxt), shop=Shop.shop_public(course, me) if why else None)


@anvil.server.callable(require_user=True)
def save_progress(course, code, position, listened=0, done=False, today=""):
    """Called by the player every ~20 s while it plays, on pause and at the end. listened = seconds actually heard
    since the last call (capped, so a stuck browser can't inflate the stats)."""
    me = C.require_user()
    if not Catalog.can_play(me, course, code):
        return C.fail("This lesson is locked.")
    try:
        position = max(0.0, min(float(position or 0), LESSON_SECONDS))
        listened = max(0.0, min(float(listened or 0), 120.0))
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
