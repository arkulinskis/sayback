# Spoken Miles

The shop and listening app for **Spoken Miles** (formerly Sayback, renamed 2026-11-23): Pimsleur-style audio language
courses made for the car. You hear a phrase in English, say it out loud in the new language in the pause, then hear the
answer. 45 minutes a lesson, 5 levels × 30 lessons per language:

| Course | Who it's for | Ad page |
|---|---|---|
| **Spoken Miles Spanish** (`en-es`) | English speakers learning Spanish | `#learn/spanish` |
| **Spoken Miles French** (`en-fr`) | English speakers learning French | `#learn/french` |
| **Spoken Miles Italian** (`en-it`) | English speakers learning Italian | `#learn/italian` |
| **Spoken Miles Inglés** (`es-en`) | Spanish speakers learning English (page in Spanish) | `#es` |

Pay once, lifetime access. Stream, save offline on the phone (a pack of 5, a level, the whole course) or download MP3s.
Gifts with a printable card. Built on [Anvil](https://anvil.works) as native Anvil Forms.

- **App repo:** github.com/arkulinskis/sayback (branch `master`; the folder and key stay `sayback`). Anvil pulls `master`.
- **Live:** https://spokenmiles.com · **Domain planned:** https://spokenmiles.com
- **The course itself** (sentences, scripts, audio): `Documents/CLAUDE/sayback` and `Documents/CLAUDE/sayback-audio`.
- **Costs and pricing:** `Documents/CLAUDE/sayback/PRICING.md` (kept out of this public repo).

## What it does

**Front door and ad pages (Persuade)**
- `#landing`: "I speak English / Español" + "I want to learn Spanish / French / Italian" (or English) -> the course page.
  Below: speaking vs tapping (a comparison table and a fair Duolingo FAQ), the car day, the gift band, FAQ.
- `#learn/<spanish|french|italian>`: one template for the three languages (words that change are `<span data-v>`,
  filled from `VALUES` in Pages/Landing). The live road demo (90 s of lesson 1), the car promise, the method, speaking vs
  tapping, the three beliefs, the 30 Level 1 lessons, offline, the offer (Level 1, complete, every language), gift link,
  "Speak or it's free" guarantee, FAQ.
- `#es`: the page for Spanish speakers (English course), written whole in Spanish.
- `#gift[/<course>]`: "Give Dad a language for the road": pick the language, give Level 1 / the complete course / every
  language; "Your gifts" for givers.
- **Ad tracking** (client_code/ads.py): UTM tags (before or after the hash), gclid/fbclid and the landing page are kept
  first-touch for 60 days in the browser (no cookies, no scripts) and saved on the account at sign-up (`users.ad_source`).

**Buying**
- Prices (2026-11-26): **$15 a level** (Levels 1 to 5 sold one by one), **$59 the whole course**, $119 every language
  (`trio` = Spanish + French + Italian). Levels you own count toward the course: the "rest of the course" offer costs
  $59 minus $15 per owned level, a level never costs more than that, and once the paid levels reach $59 the last level
  unlocks free. Change prices in Admin > Shop & setup.
- Checkout: with the App Secret `stripe_secret_key`, Shop.checkout creates a **Stripe Checkout Session** at the exact
  price (nothing to set up in Stripe). Without it, Payment Links pasted per product in Admin are a fallback (fixed prices,
  no credit). Codes: `<short>1`..`<short>5`, `<short>all`, `trio` (old `<short>up` kept for old purchases) in
  `client_code/courses.py` (shared with the server).
- Opened with `client_reference_id=<user>-<product>` (a gift: `<user>-g<product>`) and the email filled in.
- The Stripe webhook (`/_/api/stripe`, signed) unlocks lessons the moment people pay (the bundle = 3 purchase rows, the
  amount on the first), or makes a **gift code** for a gift. `charge.refunded` locks them again (also an opened gift).
- `#thanks/<product>` waits for the unlock (or the gift) and offers the next lesson (or the gift card).
- Before any link is set, buy buttons collect **waitlist** emails. Admins can give any product to any email.

**Gifts**
- `#gift/card/<code>`: the giver adds a name and a message, prints the card (print CSS shows only the card) or copies the link.
- `#redeem/<code>` (or `#redeem` + type the code): the card, then a free account and "Open my gift" -> their library.
  Codes are 12 letters/digits, open once, never expire. Admin can make free codes (giveaways). Table `gifts`.

**Library, lessons, offline (Operate)**
- `#home[/course[/level]]`: Up next (play, resume, car mode, trip length), weekly goal ring, streak with a rest day,
  14-day chart, levels and lessons, offers. Switch: Spanish · French · Italian · English.
- `#lesson/<course>/<code>[/play|/car]`: the player (±10 s, chapter marks, speed, lock-screen/car controls, car mode,
  trip length, thinking time, never-lose-your-place), phrase sheet with quiz mode, culture moment, MP3 + transcript.
  A lesson saved on the phone plays from there (blob URL, no data); with no connection it opens from what was saved.
- **Background play:** HTML audio + Media Session keep playing with the screen locked; the extra thinking-time hold is
  skipped while the page is hidden (phones won't restart audio from a timer), the recorded pause still plays.
- `#downloads[/course]` (menu: Offline): space used/free, "Save every lesson I own", per level six packs of 5 (tap to save,
  tap a saved one to remove), Save level / Remove / MP3 files, saved lessons with Play, "Put it on your home screen"
  (install prompt, iPhone steps). Engine `theme/assets/sb-offline.js` (Cache Storage). When the app opens offline,
  start-up uses the last account and the Library sends people here.

**Admin** (`#admin/...`, English): Overview (revenue, setup checklist), Sales, **Customers** (every account: what they own,
how, spent, gifts, minutes, ad source; CSV), **Ads** (sign-ups/buyers/conversion/revenue per source·campaign·page, and an
ad link builder), **Gifts** (all gifts, make a free code), Waitlist, Shop & setup (prices incl. the bundle, 13 Payment
Links, webhook, audio), Feedback, Users, Demo data.

## Setting it up in Anvil (once)

1. Anvil editor: **Create app → Clone from GitHub**, paste `https://github.com/arkulinskis/sayback`.
2. Check the **Users** service (email + password, Continue with Google, sign-up on) and the **App Secrets** service.
3. Accept the **Schema Mismatch** alert with **"The schema of the source code is correct"** (new: table `gifts`, column
   `users.ad_source`).
4. Rename the app to **Spoken Miles** (Settings > General; also what "Add to home screen" shows), then **Publish**.

## Before selling (Admin > Shop & setup shows the same checklist)

1. **Lesson audio** (4 courses, 600 lessons, about 12.9 GB).
   - Cloudflare: R2 > Create bucket (private, e.g. `spokenmiles-audio`), then R2 > Manage API tokens (Object Read & Write).
   - Upload: in `Documents/CLAUDE/sayback` run `python tools/upload_r2.py "r2://KEY:SECRET@ACCOUNT_ID/BUCKET"` (resumable).
   - **CORS rule for "save offline"** (bucket > Settings > CORS policy):
     `[{"AllowedOrigins": ["https://spokenmiles.com", "https://spokenmiles.com"], "AllowedMethods": ["GET", "HEAD"], "AllowedHeaders": ["*"], "MaxAgeSeconds": 86400}]`
   - In the Anvil editor, add the App Secret `r2_url` with that same `r2://...` text.
2. **Stripe**: App Secret `stripe_secret_key` (a restricted key with Checkout Sessions: Write is enough); webhook to
   `<app>/_/api/stripe` with `checkout.session.completed`, `checkout.session.async_payment_succeeded` and
   `charge.refunded`; its signing secret in the App Secret `stripe_webhook_secret`. Gifts need nothing extra.
3. Prices live in Admin > Shop & setup only (no products to create in Stripe).

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [Cloudflare R2](https://developers.cloudflare.com/r2/) | Outside web service | the 300 lesson MP3s and transcripts, played through 6-hour signed links |
| [Firebase Hosting](https://firebase.google.com/docs/hosting) | Outside web service | the sales pages' 90-second lesson previews (arkvital-media) |
| [Stripe Payment Links](https://stripe.com/payments/payment-links) | Outside web service | A ready-made Stripe checkout page for one product or price, shared as a link. |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Atkinson Hyperlegible, Bricolage Grotesque |

**Built into the browser:** Media Session API (lesson title on the lock screen and car display; play, pause, 10 s skips, next lesson), Screen Wake Lock, localStorage, Clipboard, File downloads (Blob), Storage API, Install prompt (Add to Home Screen), Cache Storage.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Email, Anvil JS bridge (anvil.js), Anvil Secrets, Anvil Users, Anvil Google service, Anvil HTTP, Anvil timezones (anvil.tz), Anvil Media.

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML, imageio-ffmpeg.

<!-- libraries:end -->

## Working on it

See `.claude/skills/sayback/SKILL.md`. In short:

```
python tools/check.py                    # Anvil's validator, JS syntax, asset hashes, server tests -> ALL CHECKS PASSED
python -I tools/ui_test.py               # the real app in the Anvil App Server (Docker) driven by headless Chrome
python -I tools/ui_test.py --shots DIR   # + screenshots of every page (desktop/phone, light/dark, guest/member)
python tools/make_catalog.py             # after a lesson changes in the sayback folder (writes server_code/lessons_data.py)
python tools/make_landing_lists.py       # then the Level 1 lists on both sales pages
python tools/make_hero.py                # the hero clips + timings (new file name -v2 if a clip changes; deploy media)
python tools/i18n_es.py                  # the Spanish for the member pages (and checks nothing is missing)
git push origin master                   # deploy
```

## Project layout

```
client_code/    startup.py, router.py, state.py, i18n.py, shop.py, auth.py, legal.py
                courses.py (the courses + products, shared with the server), ads.py (first-touch ad tags)
                Layouts/Shell; Pages/ Choose (#landing), Landing (#learn/<lang>), LandingEs (#es), Gift, Redeem, Downloads,
                Auth, Library (#home), Lesson, Buy, Thanks, Profile, Admin
                Components/ RoadDemo (hero engine), Player (lesson player); Dialogs/Waitlist
                Items/ LessonTile, LevelChip, DayBar, PairRow, ProductCard, PurchaseRow, SaleRow, WaitRow, NavLink, GiftRow,
                PackRow, SavedRow, LinkRow, CustomerRow, AdRow, GiftAdminRow, ...
server_code/    Catalog.py (courses, access), Listening.py (library, lesson, progress, stats), Shop.py (prices, Stripe,
                webhook, waitlist, admin shop), Gifts.py (gift codes, redeem), Customers.py (ad source, Admin customers + ads),
                Audio.py (R2 signed links), lessons_data.py + cues_data.py (generated), DemoData.py,
                Accounts.py, Admin.py, Feedback.py, SchemaCheck.py, legal_server.py, common.py
theme/assets/   app.css, sb-road.js (hero), sb-player.js (player + car mode), sb-offline.js (saved lessons, install), sb-i18n.js (Spanish), sb-hero-data.js
                (generated), app-kit.js, theme.css (spinner), icons
tools/          make_catalog.py, make_landing_lists.py, make_hero.py, i18n_keys.py, i18n_es.py, check.py, ui_test.py + ui/,
                testing/ (server tests, audio_server.py = local stand-in for R2)
```
