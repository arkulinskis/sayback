"""Demo content, so the admin pages never look empty. Loaded automatically the first time anyone opens the library
(ensure_loaded), removed or reloaded from Admin -> Demo data. Removing it is remembered: it doesn't come back.

Demo people have is_demo=True and @example.com emails; they can't sign in (no password). Every demo row is flagged
is_demo=True, so remove() deletes exactly what load() added. All names are made up.
"""
import datetime as dt

from anvil.tables import app_tables

from . import common as C

# name, email, course, product (or None), days listened in the last two weeks, lessons done
DEMO_USERS = [
    ("Maya Chen", "maya.demo@example.com", "en-es", "esall", [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11], 23),
    ("Diego Ramírez", "diego.demo@example.com", "es-en", "enall", [0, 1, 2, 4, 5, 6, 8, 9, 12], 31),
    ("Hannah Okafor", "hannah.demo@example.com", "en-es", "es1", [1, 2, 3, 5, 8], 9),
    ("Lucía Fernández", "lucia.demo@example.com", "es-en", "en1", [0, 2, 3], 4),
    ("Tom Bergström", "tom.demo@example.com", "en-es", None, [3], 1),
]
DEMO_WAITLIST = [
    ("priya.demo@example.com", "en-es", "instagram"),
    ("andres.demo@example.com", "es-en", "landing-es"),
    ("kate.demo@example.com", "en-es", "landing"),
    ("valentina.demo@example.com", "es-en", "facebook"),
]
PRICES = {"es1": 3900, "esall": 12900, "en1": 3900, "enall": 12900}
LEVELS = {"es1": [1], "en1": [1], "esall": [1, 2, 3, 4, 5], "enall": [1, 2, 3, 4, 5]}
# Tables that hold demo rows (each has an is_demo column). Children before parents.
DEMO_TABLES = ["listening", "progress", "purchases", "waitlist"]


def state():
    return C.get_setting("demo", "never")  # "never" | "loaded" | "removed"


def ensure_loaded():
    """Call from the app's main data callables: loads the demo once, unless an admin removed it."""
    if state() == "never":
        load()


def load():
    remove(remember=False)
    today = C.now().date()
    for i, (name, email, course, product, days, done) in enumerate(DEMO_USERS):
        u = app_tables.users.get(email=email) or app_tables.users.add_row(email=email, enabled=False)
        u.update(display_name=name, is_demo=True, signed_up=C.now() - dt.timedelta(days=20 + 3 * i))
        if product:
            app_tables.purchases.add_row(user=u, email=email, product=product, course=course, levels=LEVELS[product],
                                         amount=PRICES[product], currency="USD", source="stripe", session=None,
                                         payment_intent=None, note="Demo purchase", refunded=False,
                                         created=C.now() - dt.timedelta(days=18 + 2 * i), is_demo=True)
        for d in days:
            app_tables.listening.add_row(user=u, course=course, day=today - dt.timedelta(days=d),
                                         seconds=2000 + (d * 377 + i * 191) % 1400, is_demo=True)
        for n in range(done):
            lv, k = divmod(n, 30)
            app_tables.progress.add_row(user=u, course=course, code="L%d-%02d" % (lv + 1, k + 1), position=0, done=True,
                                        completions=1, updated=C.now() - dt.timedelta(days=done - n), is_demo=True)
    for j, (email, course, source) in enumerate(DEMO_WAITLIST):
        app_tables.waitlist.add_row(email=email, course=course, user=None, source=source, consent="Demo entry",
                                    created=C.now() - dt.timedelta(days=j + 1, hours=3 * j), is_demo=True)
    C.set_setting("demo", "loaded")
    return counts()


def remove(remember=True):
    for name in DEMO_TABLES:
        for r in getattr(app_tables, name).search(is_demo=True):
            r.delete()
    for u in app_tables.users.search(is_demo=True):
        u.delete()
    if remember:
        C.set_setting("demo", "removed")
    return counts()


def counts():
    out = {"users": len(app_tables.users.search(is_demo=True))}
    for name in DEMO_TABLES:
        out[name] = len(getattr(app_tables, name).search(is_demo=True))
    return out
