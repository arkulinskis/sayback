from anvil import *

from ._anvil_designer import SavedRowTemplate
from ... import i18n, router, state


class SavedRow(SavedRowTemplate):
    """One lesson saved on this phone (Downloads page). item = {course, code, title {en, es}, mb, lang}.
    Play opens the lesson (it plays from the phone, even with no signal); the bin removes it (x-remove)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.what.text = "%s · %s" % (it["code"], i18n.pick(it["title"]))
        self.meta.text = "%s · %d MB" % (it["lang"], round(it["mb"] or 0))
        state.set_attr(self.play_link, "href", router.href("lesson", it["course"], it["code"]))
        state.set_attr(self.play_link, "aria-label", i18n.t("Play {title}").replace("{title}", i18n.pick(it["title"])))
        self.remove_button.tooltip = i18n.t("Remove from this phone")
        state.set_control_attr(self.remove_button, "aria-label", i18n.t("Remove from this phone"))

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self.parent.raise_event("x-remove", codes=[self.item["code"]], course=self.item["course"])
