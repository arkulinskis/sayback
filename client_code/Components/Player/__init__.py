from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import PlayerTemplate


class Player(PlayerTemplate):
    """The lesson player around theme/assets/sb-player.js. The page calls load(...) with a signed audio link;
    the engine reports listening through the tick event (position, listened seconds, done) for save_progress.
    trip (minutes, 0 = whole lesson) stops at the pep talk that fits and raises stopped(part = the part that's next);
    think (0/2/4 extra seconds) holds the audio after each prompt (cues from get_lesson); failed(wanted_to_play) lets
    the page fetch a fresh link and swap() it in at the same second. It stops (and saves) when the page closes."""

    def __init__(self, **properties):
        self._pl = None
        super().__init__(**properties)

    def load(self, src, start=0, title="", album="", marks=None, labels=None, trip=0, think=0, cues=""):
        self.stop()
        fire = anvil.js.report_exceptions
        self._pl = window.SB.player(self.dom_nodes["mount"], {
            "src": src, "start": start or 0, "title": title, "album": album, "marks": marks or [],
            "labels": labels or {}, "trip": trip or 0, "think": think or 0, "cues": cues or "",
            "onTick": fire(lambda pos, heard, done: self.raise_event("tick", position=pos, listened=heard, done=bool(done))),
            "onEnd": fire(lambda: self.raise_event("ended")),
            "onError": fire(lambda want=False: self.raise_event("failed", wanted=bool(want))),
            "onStop": fire(lambda part: self.raise_event("stopped", part=int(part))),
            "onNext": fire(lambda: self.raise_event("next"))})

    def swap(self, src, at, play=False):
        """A fresh signed link for the same lesson, at the same second (and playing again if it was)."""
        if self._pl is not None:
            self._pl.swap(src, at, bool(play))

    def set_trip(self, minutes):
        if self._pl is not None:
            self._pl.trip(minutes)

    def set_think(self, seconds):
        if self._pl is not None:
            self._pl.think(seconds)

    def position(self):
        return float(self._pl.state()["position"] or 0) if self._pl is not None else 0.0

    def is_playing(self):
        return bool(self._pl.state()["playing"]) if self._pl is not None else False

    def play(self):
        if self._pl is not None:
            self._pl.play()

    def car(self, on=True):
        if self._pl is not None:
            self._pl.car(on)

    def engine(self):
        return self._pl

    def stop(self):
        if self._pl is not None:
            self._pl.destroy()
            self._pl = None

    @handle("", "hide")
    def form_hide(self, **event_args):
        self.stop()
