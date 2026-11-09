from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import RoadDemoTemplate

LABELS = {
    "en": {"play": "Hear 90 seconds of lesson 1", "pause": "Pause", "again": "Hear it again", "listen": "You hear",
           "say": "Your turn: say it in Spanish", "repeat": "Say it after the voice", "answer": "Then you hear",
           "failed": "The sample didn't load. Check your connection and try again."},
    "es": {"play": "Escucha 90 segundos de la lección 1", "pause": "Pausa", "again": "Escúchalo otra vez",
           "listen": "Escuchas", "say": "Tu turno: dilo en inglés", "repeat": "Repítelo después de la voz",
           "answer": "Y después escuchas", "failed": "La muestra no cargó. Revisa tu conexión y vuelve a intentarlo."},
}


class RoadDemo(RoadDemoTemplate):
    """The landing hero's live demo. The engine is mounted when the component is on screen (it measures the road)
    and stopped when the page closes, so the sample never keeps playing on another page."""

    def __init__(self, **properties):
        self._course, self._lang, self._rd = "en-es", "en", None
        super().__init__(**properties)

    @property
    def course(self):
        return self._course

    @course.setter
    def course(self, value):
        self._course = value if value in ("en-es", "es-en") else "en-es"

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, value):
        self._lang = value if value in LABELS else "en"

    @handle("", "show")
    def form_show(self, **event_args):
        self.stop()
        if not window.get("SB") or not window.SB.get("road"):
            return  # the still frame in the template stays
        self._rd = window.SB.road(self.dom_nodes["mount"], {
            "course": self._course, "labels": LABELS[self._lang],
            "onEnd": anvil.js.report_exceptions(lambda: self.raise_event("ended"))})

    @handle("", "hide")
    def form_hide(self, **event_args):
        self.stop()

    def stop(self):
        if self._rd is not None:
            self._rd.destroy()
            self._rd = None

    def engine(self):
        """The running engine (tests call state() on it)."""
        return self._rd
