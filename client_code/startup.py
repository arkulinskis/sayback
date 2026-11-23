"""The app starts here (anvil.yaml: startup module). One server call to learn who is signed in (Anvil's loading
spinner shows meanwhile), the Privacy & Terms kit, then the page for the address in the browser bar."""
import anvil.server

from . import ads, legal, router, state
from . import session_guard

session_guard.start()  # an expired server session reloads quietly instead of "Session expired, refresh now"

LEGAL_THEME = {"accent": "#b53b18"}  # colours for the Privacy & Terms page (match --c-brand in app.css)

legal.setup(LEGAL_THEME)
ads.capture()  # first-touch ad tags (utm_*) and the landing page, kept in this browser
try:
    _me = anvil.server.call("get_me")
    state.store_set("sm.me", _me)
except anvil.server.AppOfflineError:
    # No connection (a tunnel, a car park): open with the last account so saved lessons still play (#downloads).
    _me = state.store_get("sm.me")
    state.OFFLINE["on"] = True
state.set_me(_me)
if state.me() and not state.OFFLINE["on"]:
    legal.refresh_soon()
    ads.send()
router.start()
