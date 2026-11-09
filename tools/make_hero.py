"""Make the landing hero's audio clips and their timing data.

    python tools/make_hero.py

For each course it cuts ~90 s of real practice from lesson L1-01 (starting at the first phrase, after the intro),
fades it in and out, and writes:
  APP_MAKER/media/public/sayback/<course>-hero-v1.mp3   (served by arkvital-media.web.app; deploy with firebase)
  theme/assets/sb-hero-data.js                       window.SB_HERO = {course: {src, length, parts: [...]}}
parts = [start, end, kind, text] with kind p (prompt), a (answer), say (your turn), rep (repeat after the speaker).
A new file name (-v2 ...) is needed whenever a clip changes: the media site caches files for a year.
"""
import json
import pathlib
import subprocess

import imageio_ffmpeg

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAYBACK = ROOT.parent / "sayback"
AUDIO = ROOT.parent / "sayback-audio"
MEDIA = ROOT.parent / "APP_MAKER" / "media" / "public" / "sayback"
OUT = ROOT / "theme" / "assets" / "sb-hero-data.js"
BASE = "https://arkvital-media.web.app/sayback/"
VERSION = "v1"
LENGTH = 92.0                      # seconds of practice in the clip
THINK, NEW_LEAD, REPEAT_PAD = 3.0, 0.6, 1.5   # the same timing as sayback/tools/sayback.py


def parts_for(events, start, end):
    out = []
    for e in events:
        if e["kind"] == "narr":
            continue
        t, pd, ad = e["t"], e["pd"], e["ad"]
        if e["kind"] == "new":
            a1 = t + pd + NEW_LEAD
            rep = a1 + ad
            a2 = rep + ad + REPEAT_PAD
            segs = [(t, t + pd, "p", e["p"]), (a1, a1 + ad, "a", e["a"]), (rep, a2, "rep", e["a"]), (a2, a2 + ad, "a", e["a"])]
        else:
            say = t + pd
            a = say + THINK + ad
            segs = [(t, t + pd, "p", e["p"]), (say, a, "say", e["a"]), (a, a + ad, "a", e["a"])]
        if segs[0][0] < start:
            continue
        if segs[-1][1] > end:
            break
        out += [[round(s - start, 2), round(f - start, 2), k, txt] for s, f, k, txt in segs]
    return out


def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    data = {}
    for course in ("en-es", "es-en"):
        plan = json.loads((SAYBACK / "plans" / course / "L1-01.json").read_text(encoding="utf-8"))
        first = next(e for e in plan["events"] if e["kind"] != "narr")
        start = first["t"] - 0.8
        parts = parts_for(plan["events"], start, start + LENGTH)
        length = round(parts[-1][1] + 2.2, 2)
        src = next((AUDIO / course / "L1").glob("L1-01 *.mp3"))
        name = "%s-hero-%s.mp3" % (course, VERSION)
        subprocess.run([ff, "-y", "-v", "error", "-ss", "%.2f" % start, "-t", "%.2f" % length, "-i", str(src),
                        "-af", "afade=t=in:d=0.6,afade=t=out:st=%.2f:d=2" % (length - 2.0),
                        "-ac", "1", "-b:a", "64k", "-id3v2_version", "3",
                        "-metadata", "title=%s, lesson 1 (preview)" % plan["title"].get("en", "Sayback"),
                        "-metadata", "artist=Sayback", str(MEDIA / name)], check=True)
        data[course] = {"src": BASE + name, "length": length, "parts": parts}
        print("%s: %s (%.0f s, %d parts, %d KB)" % (course, name, length, len(parts), (MEDIA / name).stat().st_size // 1024))
    OUT.write_bytes(("/* Made by tools/make_hero.py: timings of the landing hero's lesson clips. Don't edit by hand. */\n"
                     "window.SB_HERO = %s;\n" % json.dumps(data, ensure_ascii=False)).encode("utf-8"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
