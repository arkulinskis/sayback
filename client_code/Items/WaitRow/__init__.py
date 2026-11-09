from anvil import *

from ._anvil_designer import WaitRowTemplate
from ... import state


class WaitRow(WaitRowTemplate):
    """One email on the waitlist (Admin -> Waitlist)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        it = self.item
        self.email.text = it["email"]
        self.course.text = it["course_name"] + (" · " + it["source"] if it["source"] else "") + (" · demo" if it.get("demo") else "")
        self.when.text = state.short_date(it["created"])
        state.set_control_attr(self.remove_button, "aria-label", "Remove " + it["email"])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        if confirm("They won't get the opening email.", title="Remove %s?" % self.item["email"],
                   buttons=[("Cancel", False), ("Remove", True)], role="app-dialog"):
            if state.call("admin_waitlist_remove", self.item["id"]):
                self.parent.raise_event("x-changed")
