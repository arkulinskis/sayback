---
name: sayback
description: Context, workflow and recipes for Sayback (folder sayback-app), the user's Anvil app built as native Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels). The shop + listening app for the Sayback audio courses (Spanish for English speakers, English for Spanish speakers): two sales pages with a live lesson demo, Stripe checkout, a waitlist, and a member library that plays the 300 lessons with progress, car mode and EN/ES. Load this before any feature request, bug fix, restyle, content change or deploy for this app.
---

# Sayback: working on the app

**What it is:** the store and player for Sayback (the course is in `Documents/CLAUDE/sayback`, the audio in
`Documents/CLAUDE/sayback-audio`: 2 courses × 5 levels × 30 lessons × 45 min). Visitors: sales page (`#landing` EN,
`#es` ES) -> free account -> lesson 1 free -> buy (Stripe Payment Link) -> library. Members: `#home` library,
`#lesson/<course>/<code>` player + phrase sheet, `#buy`, `#thanks`, `#profile`. Admin: sales, waitlist, Shop & setup.

**Where it lives:**
- Folder `C:\Users\arkvi\Documents\CLAUDE\sayback-app\` = the git clone of **github.com/arkulinskis/sayback**, branch `master`.
  "git" layout: the folder *is* the Anvil app. Anvil pulls master; pushing is the deploy. Live: not published yet.
  The folder is `sayback-app` because `sayback` is the course project.
- Made from `C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\template-forms` (native Anvil Forms, Nov 2026). Anvil's own agent
  skills describe the same model: `client-forms`, `data-models`, `server-code`, `client-modules`, `anvil-yaml`
  (github.com/anvil-works/anvil-agent-references; see APP_MAKER/ANVIL_NOTES.md, "Native Anvil Forms").
- **README.md** lists every feature. Keep it up to date.

**What the user wants:** "build the sales page for the product we created" + "we are trying to get all the learners to
buy this", people listen in stolen moments (car, cleaning), specific sales focus (Expert Secrets: the Stolen-Minutes
Method, big domino = speaking out loud in time you already lose, three false beliefs, stack, guarantee; no fake
testimonials or scarcity). Design "Morning commute": bg #eef2f4, ink #14212b, brand tail-light orange #b53b18 (bright
#e4572e = `--c-signal`, decoration only), road teal #196b7b, asphalt `--c-road`; Bricolage Grotesque + Atkinson
Hyperlegible; 14px radius, soft low shadows; dark "windshield" panels (hero, Up next, player) in both modes.
Audio delivery chosen: listen in the app, files in a private Cloudflare R2 bucket. Claude assumes
details and builds; Claude deploys. Mobile-first: every page must fit 390 px. Light and dark.

## Workflow for any change

1. `git pull --ff-only` (Anvil commits "Edited ..." when the user changes something in the IDE; read those commits).
2. Edit: a page's template and Python side by side (`client_code/Pages/X/form_template.html` + `__init__.py`).
3. `python tools/check.py` (no -I) -> **ALL CHECKS PASSED**: Anvil's validator (`anvil validate`, type-checks every
   template and Python file against Anvil's API), JS syntax, asset hashes (`tools/assets.py`), server tests.
   Needs the Anvil CLI once: `npm install -g @anvil-works/anvil-cli`.
4. `python -I tools/ui_test.py` (Docker Desktop running) -> **ALL UI TESTS PASSED**: the folder runs as-is in the
   open-source Anvil App Server (container `sayback-dev`) and headless Chrome walks tools/ui/flow.js, phone.js
   (true 390 px, no sideways scroll), admin.js and a11y.js (axe-core WCAG 2.2 AA on every page, light + dark, plus
   keyboard checks). Client edits show on reload; server edits need `--restart`. `--only a11y.js` runs one script.
   `--shots DIR` = screenshots of every page, desktop + phone, light + dark, guest + member: Read them.
5. Commit only your files as arkulinskis with the Co-Authored-By line; `git push origin master`.
   New tables/columns: tell the user to accept the **Schema Mismatch** alert ("The schema of the source code is correct").

## Architecture

```
anvil.yaml                 startup: module `startup`; db_schema; services; head_html (fonts, Prepsto, theme assets with ?v=)
client_code/
  startup.py               get_me, Privacy & Terms kit, router.start()
  router.py                PAGES (who may open each page), NAV (main menu), _form (page -> Form), go/href/replace
  state.py                 me(), call() (expected {"ok": False} -> toast + None), toast(), store, set_attr, dates
  auth.py                  sign in / up / reset / Continue with Google / sign out
  legal.py                 Privacy & Terms (installed from APP_MAKER/legal-kit; don't edit here)
  Layouts/Shell            header + account menu + footer + phone tab bar; slot "content"; refresh(page)
  Pages/                   Landing, Auth, Home (EXAMPLE), Profile, Admin (overview, feedback, users, demo data)
  Components/              custom components (Initials = the example); wrap any JS engine here
  Items/                   RepeatingPanel item templates: NavLink, ItemCard (EXAMPLE), FeedbackRow, UserRow
  Dialogs/                 dialog Forms for alert(): AddItem (EXAMPLE)
server_code/               common.py (C.*), Accounts, Admin, DemoData, Feedback, ExampleItems (EXAMPLE), SchemaCheck
theme/assets/              app.css (tokens + pages + the role layer), icons.css (generated), app-kit.js, theme.css
                           (loading spinner), icon.svg + PNGs (tools/make_icons.py)
tools/                     check.py, assets.py, build_icons.py, make_icons.py, ui_test.py + ui/, live/drive.mjs, testing/
```

## How things are done here

- **Page** = `client_code/Pages/X/` with `<anvil-form layout="Sayback.Layouts.Shell"><anvil-block slot="content">`
  and `class X(XTemplate)` taking `args=()` (the URL parts after `#x/`). Register it in router.py: `PAGES`, `_form`,
  and `NAV` if it belongs in the menu (max 4). Add its address to tools/ui/phone.js and its journey to flow.js.
- **The layout is reused between pages** (open_form keeps the Shell when the layout matches): anything in the Shell
  that depends on the user or the page goes in `Shell.refresh(page)`.
- **Navigation** = plain `<a href="#page">`; in code `router.go("page", arg)`; build links with `router.href`.
- **Static copy** = plain HTML in the template. **Text that changes** = a `Label` (role for the look).
- **Actions** = Anvil `Button` + `@handle("name", "click")`, roles `["btn", "btn-primary", "ic-plus"]`. Button roles
  are aliases of `.ui-btn` in app.css: `btn-primary`, `btn-ghost`, `btn-danger` + `btn-solid`, `btn-sm`, `btn-lg`,
  `btn-icon`, `btn-block`. Icons: role `ic-<name>` on Buttons/Links, `<i class="ic ic-<name>">` in HTML
  (names in app-kit.js `UI.ICONS`; add one there and run tools/build_icons.py).
- **Inputs** = TextBox / TextArea / DropDown / CheckBox (styled by app.css through `.ui input`, `.ui textarea`).
  Read `.text` / `.selected_value` / `.checked`; `pressed_enter` for Enter.
- **Plain HTML that changes** = `anvil:name="x"`, then `self.x.visible`, `self.x.classes["on"] = ...`,
  `self.x.style[...]`; attributes with `state.set_attr(self.x, "href", ...)`. Native clicks:
  `anvil:on-dom:click="self.x_click"` + `def x_click(self, event)`.
- **Lists** = `RepeatingPanel` + an `Items/` Form; never build repeated HTML strings. Bind fields in the item template
  (`bind:text="self.item['title']"`). Grid/flex CSS goes on the panel's items container: `.anvil-role-<role> > div`.
  Item -> page: `self.parent.raise_event("x-something", ...)` + `panel.add_event_handler("x-something", ...)`.
  Role `contents` lets a panel's items join the surrounding grid.
- **Dialogs** = a Form in `Dialogs/`, `alert(Form(...), buttons=[], role="app-dialog")`; it closes itself with
  `self.raise_event("x-close-alert", value=...)`. Yes/no: `confirm(text, title=..., buttons=[("Cancel", False), ("Delete", True)])`.
- **Toasts** = `state.toast(msg, "ok" | "error")` (Anvil Notification with roles).
- **Server calls** = `state.call("fn", ...)` for normal flows (expected `{"ok": False, "error"}` -> toast, returns None);
  a page that shows a friendly state instead (not found, private) calls `anvil.server.call` and checks `ok` itself.
  Server functions: `@anvil.server.callable(require_user=True)`, `C.require_user()` / `C.require_admin()`, ownership
  checks, return plain dicts (`C.ok(...)` / `C.fail("...")`), never other people's emails. Tables are `client: none`.
- **JavaScript** only for engines Python is too slow for (canvas, SVG drawing, WebGL, audio, maps, PDF): put it in
  `theme/assets/<name>.js`, load it in head_html (then `python tools/assets.py`), wrap it in one Python module
  (`from anvil.js import window`) and/or a `Components/` custom component. Little Hero Books is the worked example.

- **Accessibility (WCAG 2.2 AA, the legal bar; 2026-11-04)**: tools/ui/a11y.js runs axe-core on every page (light +
  dark, guest + member) and fails on serious problems; add new pages to its PUBLIC/MEMBER lists. The rules:
  - Text colours reach 4.5:1 on every surface: check new tokens (`--c-faint`, `--c-accent` used as text, status
    colours on their `-soft` fills). Text on good/bad/warn fills is `var(--c-on-status)` (white light, ink dark).
  - Every field has a name: wrap it in `<label class="ui-field"><span>Caption</span>...</label>`, or
    `state.set_control_attr(box, "aria-label", "...")` when the caption isn't a label (set it AFTER `.items` on a
    DropDown: Anvil rebuilds the select). Name/email/phone/password get `autocomplete` (set_control_attr).
  - The page's title Label is a heading: `state.heading(label, 1)` (one per page; Labels render as divs).
  - Toggle buttons say they're on: `.ui-seg` buttons get aria-pressed from the "on" class automatically (app-kit.js);
    elsewhere `state.set_control_attr(btn, "aria-pressed", ...)`. Never `role="tablist"` without real tabs.
  - Messages that appear are read out: roles msg-error/msg-note get role alert/status automatically; other changing
    Labels: `state.live(label)`. Hidden text just for screen readers: Label role `sr`.
  - When a click redraws a RepeatingPanel, keep the keyboard's place: give the item's button a `data-key` and call
    `state.refocus(panel, key)` after the event (PlanPlate's Items/Chip). Buttons have no `.focus()`: `state.focus(btn)`.
  - Images: content images get real alt text (photos: their caption); decorative ones `alt=""`; a Button icon image
    is set to alt="" automatically. Hidden anti-spam fields: `tabindex=-1`, `autocomplete=off`.

- **Design kit (2026-11-05)**: `APP_MAKER/design/README.md` is the bar for every visual change (craft floor, the
  "AI-made" tells, motion rules, worst-case data). app.css carries its CSS between `design-kit:start/end` (easing and
  duration tokens, browser surfaces, text wrapping, press feedback, gentle reduced motion): every transition uses
  `--ease-*` / `--dur-*`, no `ease-in`, no `transition: all`, no eyebrow labels, no gradient text. Checks:
  `python -I APP_MAKER/tools/design_check.py sayback` (source; check.py prints its summary) and tools/ui/design.js
  (rendered, desktop + phone, inside ui_test.py; add new pages to its PUBLIC/MEMBER). Deliberate exceptions:
  `design-ok: <rule>` comment on the line.

## Recipes

- **New table or column:** `db_schema` in anvil.yaml (same shape as the existing tables, `client: none`), then add it
  to server tests. Deploy, then the Schema Mismatch step. Personal data -> the legal kit (below).
- **New server function:** in a server module + tests in tools/testing/test_server.py (happy path, bad input,
  someone not allowed; public ones in `PUBLIC`).
- **Demo content:** DemoData.py (`is_demo=True`, `DEMO_TABLES`, children first).
- **Restyle:** tokens at the top of app.css (light and dark blocks), fonts in head_html, the spinner in theme.css
  (`python -I APP_MAKER/tools/loaders.py apply sayback <preset>`), `LEGAL_THEME` in startup.py.
- **Icon:** edit theme/assets/icon.svg, `python -I tools/make_icons.py`, then `python tools/assets.py`.

## App recipes

- **A lesson or sentence changed** (in `sayback/content`): re-render there, then here `python tools/make_catalog.py`,
  `python tools/make_landing_lists.py`, and re-upload with `sayback/tools/upload_r2.py` (skips unchanged sizes).
- **Prices / Stripe links / free lessons / test audio address:** Admin > Shop & setup (app_settings `shop`,
  `audio_base`, `free_lessons`). Real audio: App Secret `r2_url` = `r2://KEY:SECRET@ACCOUNT/BUCKET` (Audio.py signs
  6-hour links, AWS SigV4, checked against AWS's own example in the server tests).
- **Products:** Shop.PRODUCTS (es1/esall/esup = en-es, en1/enall/enup = es-en). client_reference_id = `<row id digits
  with _>-<product>`. Offers: nothing owned -> Level 1 + complete; Level 1 owned -> Level 1 (owned) + upgrade; all -> complete (owned).
- **Spanish text:** templates mark English with `data-t` (attributes `data-ta`); Python uses `i18n.t("...")`. Add the
  Spanish in `tools/i18n_es.py`, run it (it rewrites sb-i18n.js and lists anything missing). The sales pages are two
  separate Forms (Landing, LandingEs): change both. Admin stays English.
- **Hero clip:** `tools/make_hero.py` cuts ~90 s of L1-01 per course to `APP_MAKER/media/public/sayback/<course>-hero-v1.mp3`
  + timings in sb-hero-data.js; deploy media with `firebase deploy --only hosting:arkvital-media --project arkvital`.
  Change the file name (v2) when a clip changes (cached for a year).

## Gotchas

- UI tests: `admin.js` runs first and points the audio at `tools/testing/audio_server.py` (127.0.0.1:8799, byte ranges,
  maps bucket names to the rendered files). drive.mjs has `--autoplay-policy=no-user-gesture-required`. Engines expose
  `SB._player` / `SB._road` for tests. Set `window.UI_READY = false` before clicking a link in a test, or the wait passes
  on the old page. Visiting `#es` switches the app to Spanish: tests call `SB.setLang('en')` before signing up.
- Player/hero are JS engines (sb-player.js, sb-road.js) wrapped by Components/Player and Components/RoadDemo; both stop
  on hide and the router calls `leave()` on the old page.
- `in-page links`: `<a href="#offer" data-scroll>` scrolls (router), any other `#x` routes. Links with ?utm_ don't reload.
- Prepsto: claude@claude.com is at the 60-link limit, so `__PREPSTO_CODE__` is still a placeholder (check.py lists it).


- The local App Server (1.18) lags hosted Anvil: no `HtmlComponent.attrs` (use state.set_attr), `Notification(role=)`
  raises (state.toast falls back), notifications are `.anvil-alert[data-notify]`, components are wrapped in
  `<anvil-dropzone>` (app.css: `display: contents`). app.css styles both. Test on hosted Anvil too for big changes.
- Anvil's alert() without `large=True` is a 300 px modal: our role `app-dialog` widens it.
- Headless Chrome: Anvil's service worker breaks reused profiles (drive.mjs bypasses it); phone width needs device
  emulation (`MOBILE=390,844`), windows can't go below ~500 px.
- `require_secure_passwords` rejects leaked passwords: tests use random ones.
- Heredocs in the Bash tool mangle quotes: write files with the Write tool.
- A script's `el.focus()` doesn't always match `:focus-visible`, so tests check focus rings through the CSS rules,
  not computed styles. Never put `outline: none` on `input:focus` without `:not([type=checkbox]):not([type=radio])`.
- Never write Anvil's theme-colour token pattern (percent, `color:`, name, percent) in theme.css.

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit`: change `apps/sayback.json`, then there
`python -I build.py sayback && python -I install.py sayback` (writes theme/assets/legal-kit.js,
client_code/legal.py, server_code/legal_server.py and the head_html tag), then `python tools/assets.py` and deploy.
Sign-up keeps the tick box (`legal.consent_field()` in Pages/Auth). Feedback = Prepsto only ("Submit feedback").
- Client and server modules share ONE Python package: a server module can't have the same name as a client
  package or module (server `Items.py` + client `Items/` = "Cannot resolve imported module"). The template's example
  server module is `ExampleItems.py` for that reason.
