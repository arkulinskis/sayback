from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import LessonTemplate
from ... import courses, i18n, router, state
from ..Library import today, fmt

PLAYER_LABELS = ["Play", "Pause", "Back 10 seconds", "Forward 10 seconds", "Position in the lesson", "Intro", "Part {n} of 3",
                 "Pep talk", "Wrap-up", "Car mode", "Exit car mode", "Speed", "Tap anywhere big to play or pause. Eyes on the road.",
                 "Your turn: say it out loud", "Part {n} next"]
KEYS = ["play", "pause", "back", "fwd", "position", "intro", "part", "pep", "outro", "car", "exit", "speed", "carHint",
        "turn", "partNext"]
TRIPS = (15, 30, 0)          # minutes; 0 = the whole lesson
THINKS = (0, 2, 4)           # extra seconds after each prompt
LINK_MAX_AGE = 5 * 3600 * 1000   # ms: signed audio links last 6 h, so after 5 h a returning tab gets a fresh one
QUEUED_MAX = 600             # seconds of listening one save may carry from earlier failed saves (server cap)


def trip_pref():
    v = state.store_get("sb.trip", 0)
    try:
        v = int(v or 0)
    except (TypeError, ValueError):
        v = 0
    return v if v in TRIPS else 0


def think_pref():
    v = state.store_get("sb.think", 0)
    try:
        v = int(v or 0)
    except (TypeError, ValueError):
        v = 0
    return v if v in THINKS else 0


def now_ms():
    return float(window.Date.now())


class Lesson(LessonTemplate):
    """#lesson/<course>/<code>[/play|/car]: one 45-minute lesson. The player (signed link from get_lesson, saved
    position, chapter marks, car mode, trip length, thinking time), the situation and feeling, today's 20 new phrases
    (with a quiz mode), the culture moment, downloads, mark as done, previous / next. Locked lessons show the first 3
    phrases and the offer.
    Never lose your place: every save is mirrored to the browser (sb.pos.<course>.<code> = [position, ms, unsent]);
    the newer of that and the server's position wins; seconds from failed saves are kept and sent later; an expired
    link is fetched again (once) and swapped in at the same second."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.course = args[0] if args else "en-es"
        self.code = args[1] if len(args) > 1 else "L1-01"
        self.mode = args[2] if len(args) > 2 else ""
        self.quiz = False
        self.d: dict = {}
        self._unsent = 0.0
        self._retried = False
        self._link_at = now_ms()
        self._vis = None
        try:
            d = anvil.server.call("get_lesson", self.course, self.code)
        except anvil.server.AppOfflineError:
            d = self._offline_lesson()      # no connection: a lesson saved on this phone still plays
        if d.get("ok") and d.get("url") and not d.get("offline"):
            local = self._saved_url()
            if local:
                d["url"], d["streamed"] = local, d["url"]   # saved on this phone: play it from there (no data)
        if not d.get("ok"):
            state.toast(i18n.t(d.get("error") or "That lesson doesn't exist."), "error")
            self.player_card.visible = self.locked_card.visible = self.noaudio_card.visible = self.done_card.visible = False
            return
        self.d = d
        self._fill(d)

    # ---- saved on this phone (theme/assets/sb-offline.js, Pages/Downloads) ----------------------------------------
    def _saved_url(self):
        eng = window.SB.offline if window.get("SB") and window.SB.get("offline") else None
        if eng is None or not eng.supported():
            return ""
        try:
            return eng.url(self.course, self.code) or ""
        except Exception:
            return ""

    def _offline_lesson(self):
        """The lesson as saved by the Downloads page, shaped like get_lesson's answer (no links, no shop)."""
        eng = window.SB.offline if window.get("SB") and window.SB.get("offline") else None
        m = eng.meta(self.course, self.code) if eng is not None and eng.supported() else None
        url = self._saved_url() if m else ""
        if not m or not url:
            return {"ok": False, "error": "You're offline, and this lesson isn't saved on this phone. Save lessons on the Offline page before your drive."}
        def brief(x):
            return {"code": x["code"], "title": {"en": x["code"], "es": x["code"]}, "locked": False} if x else None
        return {"ok": True, "offline": True, "course": m["course"], "name": m["name"], "code": m["code"],
                "level": m["level"], "n": m["n"], "level_name": dict(m["level_name"]), "title": dict(m["title"]),
                "situation": dict(m["situation"]), "emotion": dict(m["emotion"]), "culture": m["culture"],
                "marks": list(m["marks"]), "locked": "", "free": False, "pairs": [list(x) for x in m["pairs"]],
                "pair_count": m["pair_count"], "url": url, "download": None, "transcript": None, "audio": True,
                "position": 0, "done": False, "updated": 0, "cues": m["cues"] or "",
                "prev": brief(m["prev"]), "next": brief(m["next"]), "shop": None}

    # ---- where you were -------------------------------------------------------------------------------------------
    def _pos_key(self):
        return "sb.pos.%s.%s" % (self.course, self.code)

    def _remember(self, position, unsent):
        state.store_set(self._pos_key(), [int(position or 0), now_ms(), int(unsent or 0)])

    def _start_position(self, d):
        """The server's position, unless this browser saved a newer one (a save that didn't reach the server)."""
        start = d["position"]
        loc = state.store_get(self._pos_key())
        try:
            if loc is not None and len(loc) >= 2:
                lpos, lat = float(loc[0] or 0), float(loc[1] or 0)
                self._unsent = float(loc[2] or 0) if len(loc) > 2 else 0.0
                if lat > float(d.get("updated") or 0) and abs(lpos - start) > 2:
                    start = int(lpos)
        except Exception:
            pass
        return start

    def _fill(self, d):
        self.title.text = i18n.pick(d["title"])
        state.heading(self.title, 1)
        self.meta.text = "%s · %s · %s" % (d["name"], i18n.t("Level {n}").replace("{n}", str(d["level"])),
                                           i18n.t("Lesson {n}").replace("{n}", str(d["n"])))
        self.situation.text = i18n.pick(d["situation"])
        self.emotion.text = i18n.pick(d["emotion"])
        self.culture.text = d["culture"]
        state.set_attr(self.culture, "lang", courses.COURSES.get(d["course"], courses.COURSES["en-es"])["learner"])
        state.set_attr(self.back_link, "href", router.href("home", d["course"], d["level"]))
        state.set_attr(self.lib_link, "href", router.href("home", d["course"], d["level"]))
        state.set_attr(self.unlock_link, "href", router.href("buy", d["course"]))
        locked = d["locked"]
        playable = not locked and bool(d["url"])
        self.player_card.visible = playable
        self.locked_card.visible = bool(locked)
        self.noaudio_card.visible = not locked and not d["url"]
        self.done_card.visible = False
        self.files_card.visible = playable and bool(d.get("download"))
        if locked:
            self.locked_title.text = i18n.t("Unlock Level 1 to hear this lesson") if locked == "level1" else \
                i18n.t("This lesson is in Levels 2 to 5")
            self.locked_text.text = i18n.t("Here's a taste: the first 3 of its 20 new phrases. Pay once and every lesson in the level is yours to keep.")
        if playable:
            self._links(d)
            labels = {k: i18n.t(v) for k, v in zip(KEYS, PLAYER_LABELS)}
            start = self._start_position(d)
            self.player.load(d["url"], start, self.title.text, "%s · %s" % (d["name"], self.meta.text.split(" · ", 1)[1]),
                             d["marks"], labels, trip_pref(), think_pref(), d.get("cues") or "")
            self._resume_note(start, d["marks"])
            self._show_opts()
            self._vis = anvil.js.report_exceptions(self._on_visible)
            window.document.addEventListener("visibilitychange", self._vis)
        self._done_button(d["done"])
        target = courses.COURSES.get(d["course"], courses.COURSES["en-es"])["target"]
        self.lang_target = target
        self.sheet_note.text = (i18n.t("A taste: 3 of this lesson's 20 new phrases.") if locked else
                                i18n.t("Read them after the lesson, not while driving. Quiz yourself hides the answers: say them out loud, then tap to check."))
        self._pairs()
        self.quiz_button.visible = not locked
        for link, label, item in ((self.prev_link, self.prev_title, d["prev"]), (self.next_link, self.next_title, d["next"])):
            link.visible = bool(item)
            if item:
                state.set_attr(link, "href", router.href("lesson", d["course"], item["code"]))
                label.text = item["code"] + " · " + i18n.pick(item["title"])
        self.next_button.visible = bool(d["next"])
        self.quiz_button.text = i18n.t("Quiz yourself")
        self.next_button.text = i18n.t("Next lesson")

    def _links(self, d):
        state.set_attr(self.dl_mp3, "href", d["download"])
        state.set_attr(self.dl_txt, "href", d["transcript"])

    def _resume_note(self, start, marks):
        if start <= 20:
            return
        part = 1 + int(start >= marks[1] - 3) + int(start >= marks[2] - 3)
        at_mark = part > 1 and abs(start - marks[part - 1]) <= 5
        if at_mark:
            self.resume_note.text = i18n.t("Part {n} of 3 next. It opens with a pep talk.").replace("{n}", str(part))
        else:
            self.resume_note.text = i18n.t("Picking up where you stopped, at {t}.").replace("{t}", fmt(start))
        self.resume_note.visible = True

    # ---- trip length + thinking time ------------------------------------------------------------------------------
    def _show_opts(self):
        trip, think = trip_pref(), think_pref()
        for v, el in ((15, self.trip_15), (30, self.trip_30), (0, self.trip_0)):
            el.classes["on"] = v == trip
        for v, el in ((0, self.think_0), (2, self.think_2), (4, self.think_4)):
            el.classes["on"] = v == think
        hints = {15: "Stops at the next pep talk, about 15 minutes in, so the trip ends on a clean break.",
                 30: "Plays through one pep talk and stops at the next, about 30 minutes in.",
                 0: "Plays the whole 45 minutes."}
        text = i18n.t(hints[trip])
        if think:
            text += " " + i18n.t("After each question the audio waits {n} more seconds for you while the ring fills.").replace("{n}", str(think))
        self.opts_hint.text = text

    def trip_click(self, event):
        v = int(event.currentTarget.getAttribute("data-trip") or 0)
        state.store_set("sb.trip", v)
        self.player.set_trip(v)
        self.trip_note.visible = False
        self._show_opts()

    def think_click(self, event):
        v = int(event.currentTarget.getAttribute("data-think") or 0)
        state.store_set("sb.think", v)
        self.player.set_think(v)
        self._show_opts()

    @handle("player", "stopped")
    def player_stopped(self, part, **event_args):
        self.resume_note.visible = False
        self.trip_note.text = i18n.t("Trip done, at a clean break. Part {n} of 3 is next and opens with a pep talk.").replace("{n}", str(part))
        self.trip_note.visible = True

    # ---- the player's reports -------------------------------------------------------------------------------------
    @handle("", "show")
    def form_show(self, **event_args):
        if self.d and self.player_card.visible and self.mode in ("play", "car"):
            self.player.play()
            if self.mode == "car":
                self.player.car(True)

    @handle("player", "tick")
    def player_tick(self, position, listened, done, **event_args):
        heard = float(listened or 0) + self._unsent
        send = min(heard, QUEUED_MAX)
        self._remember(position, heard)          # if this save doesn't arrive, the browser still knows
        try:
            r = anvil.server.call_s("save_progress", self.course, self.code, position, send, done, today(), self._unsent > 0)
        except Exception:
            self._unsent = min(heard, 4 * 3600)   # offline (a tunnel): these seconds go with the next save
            return
        self._unsent = heard - send
        self._remember(position, self._unsent)
        if listened:
            self._retried = False                  # the audio plays again: a later failure may refresh the link again
        if isinstance(r, dict) and r.get("newly_done"):
            self._finished()

    @handle("player", "ended")
    def player_ended(self, **event_args):
        self._finished()

    @handle("player", "failed")
    def player_failed(self, wanted=False, **event_args):
        # usually an expired 6-hour link (paused at 9 am, play at 6 pm): fetch a fresh one once, quietly
        if not self._retried:
            self._retried = True
            if self._refresh_link(wanted):
                return
        state.toast(i18n.t("The lesson audio didn't load. Check your connection, then press play again."), "error")

    def _refresh_link(self, play):
        at = self.player.position()
        try:
            d = anvil.server.call_s("get_lesson", self.course, self.code)
        except Exception:
            return False
        if not isinstance(d, dict) or not d.get("ok") or not d.get("url"):
            return False
        for k in ("url", "download", "transcript"):
            self.d[k] = d[k]
        self._links(d)
        self._link_at = now_ms()
        self.player.swap(d["url"], at, play)
        return True

    def _on_visible(self, *args):
        if window.document.visibilityState != "visible" or not self.d or not self.player_card.visible:
            return
        if self.d.get("offline") or str(self.d.get("url") or "").startswith("blob:"):
            return                                   # playing from this phone: there's no link to expire
        if now_ms() - self._link_at > LINK_MAX_AGE and not self.player.is_playing():
            self._retried = False
            self._refresh_link(False)

    @handle("player", "next")
    def player_next(self, **event_args):
        if self.d and self.d["next"] and not self.d["next"]["locked"]:
            router.go("lesson", self.course, self.d["next"]["code"], "play")

    def _finished(self):
        if self.done_card.visible:
            return
        self.done_card.visible = True
        self.trip_note.visible = False
        self._done_button(True)
        nxt = self.d["next"] if self.d else None
        if nxt and not nxt["locked"]:
            self.done_text.text = i18n.t("Tomorrow: {title}. Sleep on today's phrases; that's when they set.").replace("{title}", i18n.pick(nxt["title"]))
        elif nxt:
            self.done_text.text = i18n.t("That was the free lesson. Unlock Level 1 and tomorrow's drive is lesson 2.")
            self.next_button.visible = False
        else:
            self.done_text.text = i18n.t("That was the very last lesson. You did it: the whole course, out loud.")

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        nxt = self.d["next"]
        if nxt["locked"]:
            router.go("buy", self.course)
        else:
            router.go("lesson", self.course, nxt["code"], "play")

    @handle("quiz_button", "click")
    def quiz_button_click(self, **event_args):
        self.quiz = not self.quiz
        self.quiz_button.text = i18n.t("Show all answers") if self.quiz else i18n.t("Quiz yourself")
        state.set_control_attr(self.quiz_button, "aria-pressed", "true" if self.quiz else "false")
        self._pairs()

    def _pairs(self):
        d = self.d
        self.pairs_panel.items = [{"i": i + 1, "p": p[0], "a": p[1], "g": p[2], "hide": self.quiz, "lang": self.lang_target}
                                  for i, p in enumerate(d["pairs"])]

    def _done_button(self, done):
        self.done_button.text = i18n.t("Done. Mark as not done") if done else i18n.t("Mark as done")
        self.done_button.role = ["btn", "btn-block", "btn-ghost", "ic-check"] + (["on"] if done else [])

    @handle("done_button", "click")
    def done_button_click(self, **event_args):
        flag = "on" not in (self.done_button.role or [])
        r = state.call("set_done", self.course, self.code, flag)
        if r:
            self._done_button(r["done"])
            state.toast(i18n.t("Marked as done") if r["done"] else i18n.t("Marked as not done"), "ok")

    def leave(self):
        if self._vis is not None:
            window.document.removeEventListener("visibilitychange", self._vis)
            self._vis = None
        self.player.stop()
