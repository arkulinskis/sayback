from anvil import *
import anvil.server

from ._anvil_designer import LessonTemplate
from ... import i18n, router, state
from ..Library import today, fmt

PLAYER_LABELS = ["Play", "Pause", "Back 10 seconds", "Forward 10 seconds", "Position in the lesson", "Intro", "Part {n} of 3",
                 "Pep talk", "Wrap-up", "Car mode", "Exit car mode", "Speed", "Tap anywhere big to play or pause. Eyes on the road."]
KEYS = ["play", "pause", "back", "fwd", "position", "intro", "part", "pep", "outro", "car", "exit", "speed", "carHint"]


class Lesson(LessonTemplate):
    """#lesson/<course>/<code>[/play|/car]: one 45-minute lesson. The player (signed link from get_lesson, saved
    position, chapter marks, car mode), the situation and feeling, today's 20 new phrases (with a quiz mode), the
    culture moment, downloads, mark as done, previous / next. Locked lessons show the first 3 phrases and the offer."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.course = args[0] if args else "en-es"
        self.code = args[1] if len(args) > 1 else "L1-01"
        self.mode = args[2] if len(args) > 2 else ""
        self.quiz = False
        self.d: dict = {}
        d = anvil.server.call("get_lesson", self.course, self.code)
        if not d.get("ok"):
            state.toast(i18n.t(d.get("error") or "That lesson doesn't exist."), "error")
            self.player_card.visible = self.locked_card.visible = self.noaudio_card.visible = self.done_card.visible = False
            return
        self.d = d
        self._fill(d)

    def _fill(self, d):
        self.title.text = i18n.pick(d["title"])
        state.heading(self.title, 1)
        self.meta.text = "%s · %s · %s" % (d["name"], i18n.t("Level {n}").replace("{n}", str(d["level"])),
                                           i18n.t("Lesson {n}").replace("{n}", str(d["n"])))
        self.situation.text = i18n.pick(d["situation"])
        self.emotion.text = i18n.pick(d["emotion"])
        self.culture.text = d["culture"]
        state.set_attr(self.culture, "lang", "en" if d["course"] == "en-es" else "es")
        state.set_attr(self.back_link, "href", router.href("home", d["course"], d["level"]))
        state.set_attr(self.lib_link, "href", router.href("home", d["course"], d["level"]))
        state.set_attr(self.unlock_link, "href", router.href("buy", d["course"]))
        locked = d["locked"]
        playable = not locked and bool(d["url"])
        self.player_card.visible = playable
        self.locked_card.visible = bool(locked)
        self.noaudio_card.visible = not locked and not d["url"]
        self.done_card.visible = False
        self.files_card.visible = playable
        if locked:
            self.locked_title.text = i18n.t("Unlock Level 1 to hear this lesson") if locked == "level1" else \
                i18n.t("This lesson is in Levels 2 to 5")
            self.locked_text.text = i18n.t("Here's a taste: the first 3 of its 20 new phrases. Pay once and every lesson in the level is yours to keep.")
        if playable:
            state.set_attr(self.dl_mp3, "href", d["download"])
            state.set_attr(self.dl_txt, "href", d["transcript"])
            labels = {k: i18n.t(v) for k, v in zip(KEYS, PLAYER_LABELS)}
            start = d["position"]
            self.player.load(d["url"], start, self.title.text, "%s · %s" % (d["name"], self.meta.text.split(" · ", 1)[1]), d["marks"], labels)
            if start > 20:
                self.resume_note.text = i18n.t("Picking up where you stopped, at {t}.").replace("{t}", fmt(start))
                self.resume_note.visible = True
        self._done_button(d["done"])
        target = "es" if d["course"] == "en-es" else "en"
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

    def _pairs(self):
        d = self.d
        self.pairs_panel.items = [{"i": i + 1, "p": p[0], "a": p[1], "g": p[2], "hide": self.quiz, "lang": self.lang_target}
                                  for i, p in enumerate(d["pairs"])]

    def _done_button(self, done):
        self.done_button.text = i18n.t("Done. Mark as not done") if done else i18n.t("Mark as done")
        self.done_button.role = ["btn", "btn-block", "btn-ghost", "ic-check"] + (["on"] if done else [])

    @handle("", "show")
    def form_show(self, **event_args):
        if self.d and self.player_card.visible and self.mode in ("play", "car"):
            self.player.play()
            if self.mode == "car":
                self.player.car(True)

    @handle("player", "tick")
    def player_tick(self, position, listened, done, **event_args):
        try:
            r = anvil.server.call_s("save_progress", self.course, self.code, position, listened, done, today())
        except Exception:
            return  # offline for a moment: the next tick saves again
        if isinstance(r, dict) and r.get("newly_done"):
            self._finished()

    @handle("player", "ended")
    def player_ended(self, **event_args):
        self._finished()

    @handle("player", "failed")
    def player_failed(self, **event_args):
        state.toast(i18n.t("The lesson audio didn't load. Check your connection, then press play again."), "error")

    @handle("player", "next")
    def player_next(self, **event_args):
        if self.d and self.d["next"] and not self.d["next"]["locked"]:
            router.go("lesson", self.course, self.d["next"]["code"], "play")

    def _finished(self):
        if self.done_card.visible:
            return
        self.done_card.visible = True
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

    @handle("done_button", "click")
    def done_button_click(self, **event_args):
        flag = "on" not in (self.done_button.role or [])
        r = state.call("set_done", self.course, self.code, flag)
        if r:
            self._done_button(r["done"])
            state.toast(i18n.t("Marked as done") if r["done"] else i18n.t("Marked as not done"), "ok")

    def leave(self):
        self.player.stop()
