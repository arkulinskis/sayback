from anvil import *
from anvil.js import get_dom_node

from ._anvil_designer import PackRowTemplate
from ... import i18n, router, state

PACK = 5


class PackRow(PackRowTemplate):
    """One level on the Downloads page: six packs of 5 lessons (tap one to save it; a saved pack shows a tick),
    Save level / Remove / MP3 files. item = a level from downloads_info + course + saved (codes on this phone).
    Raises x-save / x-remove / x-files with the lesson codes; the page does the work."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.codes = [x["code"] for x in it["lessons"] if x["open"]]   # only lessons this person may hear
        saved = set(it["saved"])
        n_saved = len([c for c in self.codes if c in saved])
        self.title.text = "%s %d · %s" % (i18n.t("Level"), it["level"], i18n.pick(it["name"]))
        self.meta.text = (i18n.t("{n} lessons · {size}").replace("{n}", str(len(it["lessons"]))).replace("{size}", "%d MB" % it["mb"])
                          + (" · " + i18n.t("{n} saved").replace("{n}", str(n_saved)) if n_saved else ""))
        locked = not it["open"]
        self.buy_link.visible = locked
        state.set_attr(self.buy_link, "href", router.href("buy", it["course"]))
        self.chips_part.visible = bool(self.codes)          # a free lesson can be saved even before buying
        self.files_button.visible = not locked
        self.remove_button.visible = n_saved > 0
        self.save_button.text = i18n.t("Save level")
        self.save_button.visible = not locked and n_saved < len(self.codes)
        self.remove_button.text = i18n.t("Remove")
        self.files_button.text = i18n.t("MP3 files")
        for i, chip in enumerate((self.p1, self.p2, self.p3, self.p4, self.p5, self.p6)):
            part = self.codes[i * PACK:(i + 1) * PACK]
            chip.visible = bool(part)
            if not part:
                continue
            done = all(c in saved for c in part)
            first, last = i * PACK + 1, i * PACK + len(part)
            chip.classes["on"] = done
            label = "%d–%d" % (first, last)
            state.set_attr(chip, "aria-pressed", "true" if done else "false")
            state.set_attr(chip, "aria-label", i18n.t("Lessons {range}").replace("{range}", label) +
                           (" · " + i18n.t("saved") if done else ""))
            get_dom_node(chip).textContent = ("✓ " if done else "") + label

    def pack_click(self, event):
        i = int(event.currentTarget.getAttribute("data-pack") or 1) - 1
        part = self.codes[i * PACK:(i + 1) * PACK]
        saved = set(self.item["saved"])
        if part and all(c in saved for c in part):
            self.parent.raise_event("x-remove", codes=part)
        else:
            self.parent.raise_event("x-save", codes=[c for c in part if c not in saved])

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        saved = set(self.item["saved"])
        self.parent.raise_event("x-save", codes=[c for c in self.codes if c not in saved])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        if confirm(i18n.t("Remove this level's saved lessons from this phone? You can save them again any time."),
                   buttons=[(i18n.t("Cancel"), False), (i18n.t("Remove"), True)]):
            self.parent.raise_event("x-remove", codes=self.codes)

    @handle("files_button", "click")
    def files_button_click(self, **event_args):
        self.parent.raise_event("x-files", codes=self.codes)
