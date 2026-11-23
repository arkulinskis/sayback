"""The Spoken Miles courses and what we sell, in one place (client AND server import this module).

A course is "<learner language>-<target language>": en-es = English speakers learn Spanish. Spoken Miles sells to
English speakers learning Spanish, French and Italian, and to Spanish speakers learning English (es-en). More pairs
later = one more entry here, a column in Documents/CLAUDE/sayback/content/L*.txt and a render.

Ad pages: #learn/<slug> (spanish, french, italian) and #es (Spanish speakers). PRODUCT codes are what Stripe's
client_reference_id carries (letters and digits only): <short><kind> (es1, esall, esup, fr1, ...) and the bundle "trio".
"""

ORDER = ["en-es", "en-fr", "en-it", "es-en"]

COURSES: dict = {
    "en-es": {"slug": "spanish", "short": "es", "learner": "en", "target": "es", "lang": "Spanish",
              "name": "Spoken Miles Spanish", "sample": ["Where is the station?", "¿Dónde está la estación?"]},
    "en-fr": {"slug": "french", "short": "fr", "learner": "en", "target": "fr", "lang": "French",
              "name": "Spoken Miles French", "sample": ["Where is the station?", "Où est la gare ?"]},
    "en-it": {"slug": "italian", "short": "it", "learner": "en", "target": "it", "lang": "Italian",
              "name": "Spoken Miles Italian", "sample": ["Where is the station?", "Dov'è la stazione?"]},
    "es-en": {"slug": "ingles", "short": "en", "learner": "es", "target": "en", "lang": "English",
              "name": "Spoken Miles Inglés", "sample": ["¿Dónde está la estación?", "Where is the station?"]},
}

# What the learner speaks -> the courses offered (the landing page's "I speak ... / I want to learn ...")
FOR_LEARNER: dict = {"en": ["en-es", "en-fr", "en-it"], "es": ["es-en"]}
SPEAKS = [("en", "English"), ("es", "Español")]
TARGET_NAMES: dict = {"en": {"es": "Spanish", "fr": "French", "it": "Italian", "en": "English"},
                "es": {"es": "español", "fr": "francés", "it": "italiano", "en": "inglés"}}

ALL_LEVELS = [1, 2, 3, 4, 5]
KINDS: dict = {"level1": [1], "complete": [1, 2, 3, 4, 5], "upgrade": [2, 3, 4, 5]}


def _products():
    out: dict = {}
    for c in ORDER:
        s = str(COURSES[c]["short"])
        out[s + "1"] = {"courses": [c], "kind": "level1", "levels": KINDS["level1"]}
        out[s + "all"] = {"courses": [c], "kind": "complete", "levels": KINDS["complete"]}
        out[s + "up"] = {"courses": [c], "kind": "upgrade", "levels": KINDS["upgrade"]}
    # Every language for English speakers, lifetime: Spanish + French + Italian, all five levels.
    out["trio"] = {"courses": list(FOR_LEARNER["en"]), "kind": "bundle", "levels": KINDS["complete"]}
    return out


PRODUCTS: dict = _products()


def course_of(product):
    """The (first) course a product unlocks, for pages that show one course."""
    p = PRODUCTS.get(product)
    return p["courses"][0] if p else "en-es"


def by_slug(slug):
    for c in ORDER:
        if COURSES[c]["slug"] == (slug or "").lower():
            return c
    return None


def product_for(course, kind):
    if kind == "bundle":
        return "trio"
    return str(COURSES[course]["short"]) + {"level1": "1", "complete": "all", "upgrade": "up"}[kind]
