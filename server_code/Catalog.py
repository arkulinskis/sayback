"""The two courses, their 150 lessons each, and who may hear what.

Courses: en-es = Sayback Spanish (English speakers learn Spanish), es-en = Sayback Inglés (Spanish speakers learn
English). Lesson codes: L<level>-<nn>, e.g. L1-01. The data comes from lessons_data.py (tools/make_catalog.py).

Access: the first FREE lessons of Level 1 are free for anyone with an account (default: lesson 1); a level is open
when a purchase that isn't refunded covers it; admins hear everything.
"""
from anvil.tables import app_tables

from . import common as C
from . import lessons_data

COURSES = ("en-es", "es-en")
LEVELS = (1, 2, 3, 4, 5)
_DATA = lessons_data.DATA
_INDEX = {c: {ls["code"]: ls for ls in _DATA["courses"][c]["lessons"]} for c in COURSES}


def course_ok(course):
    return course in COURSES


def course_name(course):
    return _DATA["courses"][course]["name"]


def level_name(level, lang="en"):
    return _DATA["levels"][str(level)][lang]


def lessons(course):
    return _DATA["courses"][course]["lessons"]


def lesson(course, code):
    return _INDEX.get(course, {}).get(code)


def neighbours(course, code):
    """(previous code, next code) in course order, None at either end."""
    codes = [ls["code"] for ls in lessons(course)]
    if code not in codes:
        return None, None
    i = codes.index(code)
    return (codes[i - 1] if i > 0 else None), (codes[i + 1] if i + 1 < len(codes) else None)


def free_count():
    n = C.get_setting("free_lessons", 1)
    return n if isinstance(n, int) and 0 <= n <= 30 else 1


def is_free(code):
    return code in ["L1-%02d" % i for i in range(1, free_count() + 1)]


def live_purchases(user, course=None):
    if user is None:
        return []
    rows = app_tables.purchases.search(user=user)
    return [p for p in rows if not p["refunded"] and (course is None or p["course"] == course)]


def owned_levels(user, course):
    out = set()
    for p in live_purchases(user, course):
        out.update(int(x) for x in (p["levels"] or []) if int(x) in LEVELS)
    return out


def can_play(user, course, code):
    ls = lesson(course, code)
    if ls is None or user is None:
        return False
    if C.is_admin(user) or is_free(code):
        return True
    return ls["level"] in owned_levels(user, course)


def why_locked(user, course, code):
    """'' when it plays, else 'signin' / 'level1' / 'complete' (what the person would need)."""
    if user is None:
        return "signin"
    if can_play(user, course, code):
        return ""
    ls = lesson(course, code)
    return "level1" if ls and ls["level"] == 1 else "complete"
