"""Build server_code/lessons_data.py from the Sayback course sources (Documents/CLAUDE/sayback).

    python tools/make_catalog.py

Run it again whenever a lesson, title or sentence changes in sayback/content/L*.txt. The app reads only the
generated module (titles, situation, feeling, culture note and the 20 new sentences of every lesson), so the
course folder never has to be on Anvil. Audio files are named <course>/L<level>/L<level>-<nn>.mp3 in storage
(tools/upload_r2.py in the sayback folder uploads them under exactly these names).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAYBACK = ROOT.parent / "sayback"
AUDIO = ROOT.parent / "sayback-audio"
OUT = ROOT / "server_code" / "lessons_data.py"
sys.path.insert(0, str(SAYBACK / "tools"))
import sayback as SB  # noqa: E402

LEVELS = {
    1: {"en": "First Steps", "es": "Primeros pasos"},
    2: {"en": "Everyday Life", "es": "La vida diaria"},
    3: {"en": "Real Conversations", "es": "Conversaciones reales"},
    4: {"en": "Feelings and Stories", "es": "Sentimientos e historias"},
    5: {"en": "Fluent and Local", "es": "Fluido y local"},
}


def nice_name(course, code):
    """'Sayback Spanish L1-01 Hello and first words.mp3' from the rendered file's own name."""
    level = code.split("-")[0]
    hits = sorted((AUDIO / course / level).glob(code + " *.mp3"))
    tail = hits[0].stem[len(code) + 1:] if hits else ""
    return ("%s %s %s" % (SB.COURSES[course]["name"], code, tail)).strip() + ".mp3"


def marks(course, code):
    """[first phrase, encouragement 1, encouragement 2, outro] in seconds, from the lesson's schedule."""
    f = SAYBACK / "plans" / course / (code + ".json")
    if not f.exists():
        return [75, 900, 1800, 2670]
    ev = json.loads(f.read_text(encoding="utf-8"))["events"]
    first = next((e["t"] for e in ev if e["kind"] != "narr"), 75)
    part = {e.get("part"): e["t"] for e in ev if e["kind"] == "narr"}
    return [round(first), round(part.get("enc1", 900)), round(part.get("enc2", 1800)), round(part.get("outro", 2670))]


def main():
    data = {"levels": {str(k): v for k, v in LEVELS.items()}, "courses": {}}
    for course, meta in SB.COURSES.items():
        learner, target = meta["learner"], meta["target"]
        lessons = []
        for ls in SB.all_lessons(course):
            code = SB.lesson_key(ls)
            pairs = [[s[learner], s[target], s.get("g", "")] for s in ls["sentences"]]
            lessons.append({
                "code": code, "level": ls["level"], "n": ls["n"],
                "title": {"en": ls["title"].get("en", ""), "es": ls["title"].get("es", ls["title"].get("en", ""))},
                "situation": dict(ls.get("situation") or {}), "emotion": dict(ls.get("emotion") or {}),
                "culture": (ls.get("culture") or {}).get(target, ""),  # written in the learner's language
                "grammar": ls.get("grammar", ""),
                "file": "%s/L%d/%s.mp3" % (course, ls["level"], code),
                "download": nice_name(course, code),
                "marks": marks(course, code),
                "pairs": pairs,
            })
        data["courses"][course] = {"name": meta["name"], "learner": learner, "target": target, "lessons": lessons}
        print("%s: %d lessons, %d sentences" % (course, len(lessons), sum(len(x["pairs"]) for x in lessons)))
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_bytes(('"""Made by tools/make_catalog.py from the Sayback course files. Don\'t edit by hand."""\n'
                     "import json\n\nDATA = json.loads(%r)\n" % body).encode("utf-8"))
    print("wrote", OUT, "(%d KB)" % (OUT.stat().st_size // 1024))


if __name__ == "__main__":
    main()
