from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import PlayerTemplate


class Player(PlayerTemplate):
    """The lesson player around theme/assets/sb-player.js. The page calls load(...) with a signed audio link;
    the engine reports listening through the tick event (position, listened seconds, done) for save_progress.
    It stops (and saves one last time) when the page closes."""

    def __init__(self, **properties):
        self._pl = None
        super().__init__(**properties)

    def load(self, src, start=0, title="", album="", marks=None, labels=None):
        self.stop()
        fire = anvil.js.report_exceptions
        self._pl = window.SB.player(self.dom_nodes["mount"], {
            "src": src, "start": start or 0, "title": title, "album": album, "marks": marks or [],
            "labels": labels or {},
            "onTick": fire(lambda pos, heard, done: self.raise_event("tick", position=pos, listened=heard, done=bool(done))),
            "onEnd": fire(lambda: self.raise_event("ended")),
            "onError": fire(lambda: self.raise_event("failed")),
            "onNext": fire(lambda: self.raise_event("next"))})

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
