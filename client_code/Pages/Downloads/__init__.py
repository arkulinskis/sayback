from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import DownloadsTemplate
from ... import courses, i18n, router, state


def engine():
    return window.SB.offline if window.get("SB") and window.SB.get("offline") else None


class Downloads(DownloadsTemplate):
    """#downloads[/<course>]: lessons saved on this phone (play them with no signal), save a pack of 5 / a level /
    every lesson owned, remove them, MP3 files, and "put it on your home screen". When the app opened with no
    connection (state.OFFLINE) it only lists what's saved, for playing. Engine: theme/assets/sb-offline.js."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.heading, 1)
        self.queue, self.total_done, self.saved_codes = [], 0, {}
        self.progress_part.visible = False
        self.d = None
        self._install()
        eng = engine()
        if eng is None or not eng.supported():
            self.offline_note.text = i18n.t("This browser can't keep lessons offline. Stream them, or download the MP3 files.")
            self.offline_note.visible = True
            self.save_all_button.visible = False
        if state.OFFLINE["on"]:
            self.offline_note.text = i18n.t("You're offline. Your saved lessons still play.")
            self.offline_note.visible = True
            self.switch.visible = self.levels_part.visible = self.save_all_button.visible = False
            self.sub.text = ""
        else:
            course = args[0] if args else state.store_get("sayback.course")
            self.d = state.call("downloads_info", course)
            if self.d:
                self.course = self.d["course"]
                state.store_set("sayback.course", self.course)
                self.sub.text = self.d["name"]
                for code, el in (("en-es", self.sw_es), ("en-fr", self.sw_fr), ("en-it", self.sw_it), ("es-en", self.sw_en)):
                    el.classes["on"] = code == self.course
                if not self.d["audio"]:
                    self.offline_note.text = i18n.t("Lesson audio isn't connected yet, so nothing can be saved.")
                    self.offline_note.visible = True
        self.levels.add_event_handler("x-save", self._save_codes)
        self.levels.add_event_handler("x-remove", self._remove_codes)
        self.levels.add_event_handler("x-files", self._files)
        self.saved_list.add_event_handler("x-remove", self._remove_codes)
        self.refresh()

    # ---------------------------------------------------------------- drawing
    def refresh(self):
        eng = engine()
        saved = list(eng.saved()) if eng is not None and eng.supported() else []
        by = {}
        for s in saved:
            by.setdefault(s["course"], set()).add(s["code"])
        self.saved_codes = by
        rows: list = sorted([dict(course=s["course"], code=s["code"], mb=s["mb"], title={"en": s["title_en"], "es": s["title_es"]},
                            lang=courses.COURSES.get(s["course"], {}).get("lang", "")) for s in saved],
                      key=lambda r: (r["course"], r["code"]))
        self.saved_list.items = rows
        self.saved_part.visible = bool(rows)
        if self.d:
            self.levels.items = [dict(lv, course=self.course, saved=sorted(by.get(self.course, set())))
                                 for lv in self.d["levels"]]
        total = 0.0
        for r in rows:
            total += float(r["mb"] or 0)
        self._space(total, len(rows))

    def _space(self, mb, n):
        eng = engine()
        sp = eng.space() if eng is not None else {"used": 0, "quota": 0}
        used, quota = sp["used"], sp["quota"]
        self.space_text.text = i18n.t("{n} lessons saved ({size})").replace("{n}", str(n)).replace("{size}", fmt_mb(mb))
        free = max(0, quota - used)
        self.space_fine.text = (i18n.t("About {free} free for Spoken Miles on this device.").replace("{free}", fmt_mb(free))
                                if quota else "")
        self.space_fill.style["transform"] = "scaleX(%.3f)" % (min(1.0, used / float(quota)) if quota else 0)

    def _install(self):
        ins = window.SB.install if window.get("SB") and window.SB.get("install") else None
        if ins is None or ins.standalone():
            self.install_card.visible = False
            return
        self.install_button.visible = bool(ins.can())
        self.ios_steps.visible = bool(ins.ios())
        self.other_steps.visible = not ins.ios() and not ins.can()

    @handle("install_button", "click")
    def install_button_click(self, **event_args):
        if window.SB.install.prompt():
            self.install_card.visible = False

    # ---------------------------------------------------------------- saving
    def _save_codes(self, codes=None, **event_args):
        self.queue.append(list(codes or []))
        if not engine().busy():
            self._next()

    @handle("save_all_button", "click")
    def save_all_button_click(self, **event_args):
        if not self.d:
            return
        have = set(self.saved_codes.get(self.course, set()))
        todo = [[x["code"] for x in lv["lessons"] if x["open"] and x["code"] not in have] for lv in self.d["levels"]]
        todo = [t for t in todo if t]
        if not todo:
            state.toast(i18n.t("Every lesson you own is already saved."), "ok")
            return
        total = sum(x["mb"] for lv in self.d["levels"] for x in lv["lessons"] if x["code"] in [c for t in todo for c in t])
        if not confirm(i18n.t("Save {n} lessons ({size}) on this phone? Use Wi-Fi if you can.")
                       .replace("{n}", str(sum(len(t) for t in todo))).replace("{size}", fmt_mb(total)),
                       buttons=[(i18n.t("Cancel"), False), (i18n.t("Save them"), True)]):
            return
        self.queue.extend(todo)
        if not engine().busy():
            self._next()

    def _next(self):
        if not self.queue:
            self._busy(False)
            self.refresh()
            return
        codes = self.queue.pop(0)
        r = state.call("offline_pack", self.course, codes)
        if not r or not r["items"]:
            self._next()
            return
        engine().persist()
        self._busy(True)
        self.progress_text.text = i18n.t("Saving…")
        engine().start(r["items"], {"onProgress": anvil.js.report_exceptions(self._progress),
                                    "onDone": anvil.js.report_exceptions(self._done)})

    def _progress(self, done, total, mb):
        self.progress_fill.style["transform"] = "scaleX(%.3f)" % (done / float(total or 1))
        self.progress_text.text = i18n.t("Saved {done} of {total} ({size})").replace("{done}", str(done)) \
            .replace("{total}", str(total)).replace("{size}", fmt_mb(mb))

    def _done(self, saved, failed):
        if failed:
            state.toast(i18n.t("{n} lessons didn't save. Check your connection and try again.").replace("{n}", str(failed)), "error")
            self.queue = []
        self.refresh()
        self._next()

    def _busy(self, on):
        self.progress_part.visible = on
        self.cancel_button.visible = on
        self.save_all_button.enabled = not on

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.queue = []
        engine().cancel()

    # ---------------------------------------------------------------- removing, files
    def _remove_codes(self, codes=None, course=None, **event_args):
        engine().remove(course or self.course, list(codes or []))
        self.refresh()
        state.toast(i18n.t("Removed from this phone."), "ok")

    def _files(self, codes=None, **event_args):
        r = state.call("offline_pack", self.course, list(codes or []), True)
        if not r or not r["items"]:
            return
        engine().files([x["url"] for x in r["items"]])
        state.toast(i18n.t("Downloading {n} MP3 files. Your browser may ask to allow several downloads.")
                    .replace("{n}", str(len(r["items"]))), "ok")

    def leave(self):
        pass   # saving carries on in the background if the member opens another page


def fmt_mb(mb):
    mb = float(mb or 0)
    return ("%.1f GB" % (mb / 1000.0)) if mb >= 1000 else ("%d MB" % round(mb))
