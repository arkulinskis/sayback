from anvil import *

from ._anvil_designer import ProfileTemplate
from ... import auth, i18n, router, state


class Profile(ProfileTemplate):
    """#profile: your courses (purchases), your name, the app's language, light/dark, a password reset link,
    Privacy & Terms, feedback, sign out."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._show_me()
        self._show_theme()
        state.heading(self.name_title, 1)
        rows = state.call("my_purchases")["purchases"]
        self.purchases_panel.items = rows
        self.no_purchases.visible = not rows
        self.lang_en.classes["on"] = i18n.lang() == "en"
        self.lang_es.classes["on"] = i18n.lang() == "es"
        self.save_button.text = i18n.t("Save")
        self.reset_button.text = i18n.t("Email me a reset link")

    def _show_me(self):
        me = state.me()
        self.initials.text = state.initials(me.get("name"))
        self.name_title.text = me.get("name") or ""
        joined = state.month_year(me.get("joined"))
        self.email_line.text = (me.get("email") or "") + ((" · " + i18n.t("member since") + " " + joined) if joined else "")
        self.name_box.text = me.get("name") or ""
        self.admin_link.visible = bool(me.get("is_admin"))

    def _show_theme(self):
        t = state.theme()
        for name, el in (("auto", self.theme_auto), ("light", self.theme_light), ("dark", self.theme_dark)):
            el.classes["on"] = name == t

    def lang_click(self, event):
        i18n.set_lang(event.currentTarget.getAttribute("data-lang"))
        router.show()

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-pick"))
        self._show_theme()

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.save_button_click()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast(i18n.t("Please tell us your name."), "error")
            return
        r = state.call("update_profile", name)
        if r:
            state.set_me(r["me"])
            self._show_me()
            state.toast(i18n.t("Saved"), "ok")

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        r = auth.reset(state.me()["email"])
        state.toast(i18n.t(r["message"]), "ok")

    def feedback_click(self, event):
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast(i18n.t("Signed out. See you soon!"))
        router.go("es" if i18n.lang() == "es" else "landing")
