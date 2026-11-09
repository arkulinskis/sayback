# Sayback

The shop and listening app for **Sayback**, Pimsleur-style audio courses for stolen minutes (the commute, the dishes,
the laundry): **Sayback Spanish** (English speakers learn Spanish) and **Sayback Inglés** (Spanish speakers learn
English), 5 levels × 30 lessons × 45 minutes each. Two sales pages (English and Spanish) with a live lesson demo, a free
lesson 1 with an account, Stripe checkout, and a member library that plays every lesson with saved progress, car mode
and lock-screen controls. Built on [Anvil](https://anvil.works) as native Anvil Forms.

- **App repo:** github.com/arkulinskis/sayback (branch `master`). Anvil pulls `master`.
- **Live:** not published yet (planned: sayback.anvil.app or a custom domain).
- **The course itself** (sentences, scripts, audio): `Documents/CLAUDE/sayback` and `Documents/CLAUDE/sayback-audio`.

## What it does

**Sales pages (Persuade)**
- `#landing` (English, Sayback Spanish) and `#es` (Spanish, Sayback Inglés), each written whole in its language.
- Hero: "the windshield", a road demo. 90 seconds of the real lesson 1 play from the media site while the prompt, the
  thinking pause (with a countdown ring) and the answer drive past under a playhead. Still frame without audio.
- The Stolen-Minutes promise (a day timeline), why it works (the Pimsleur method), the 45-minute lesson timeline, the
  three false beliefs, all 30 Level 1 lessons, the five levels, "two cultures, one table", the offer with live prices,
  the "Speak or it's free" guarantee, FAQ (driving safety, AI voices), final call.
- Every buy button: visitors make a free account first, then land on `#buy/<course>/<product>` with their plan marked.

**Buying**
- Stripe Payment Links (Admin > Shop & setup), opened with `client_reference_id=<user>-<product>` and the email filled in.
- Products per course: Level 1, the complete course (Levels 1 to 5), and the upgrade (Levels 2 to 5, only offered to
  Level 1 owners).
- The Stripe webhook (`/_/api/stripe`, signed) unlocks lessons the moment people pay. `charge.refunded` locks them again
  (the guarantee).
- `#thanks/<product>` waits for the unlock and then offers the next lesson.
- Before any link is set, the buy buttons collect **waitlist** emails (one-message consent, CSV in Admin).
- Admins can give a course to any email. A gift for an email without an account joins that account when it signs up.

**Library and lessons (Operate)**
- `#home[/course[/level]]`:
  - greeting and "Up next" (play, resume at mm:ss, car mode)
  - stolen minutes this week, day streak, lessons done, a 14-day chart
  - five level chips and the 30 lessons of the chosen level (done, % heard, free, locked)
  - offers for what isn't owned yet
- `#lesson/<course>/<code>[/play|/car]`:
  - **player**: ±10 s, a scrubber with chapter marks (intro, the two pep talks, wrap-up), speed 0.85/1/1.15, lock-screen/car controls (Media Session), full-screen car mode with one giant button
  - **progress**: saved every ~20 s of listening and on pause; done at 93%
  - **lesson content**: situation and feeling, the 20 new phrases (with "quiz yourself", tap to reveal), the culture moment, MP3 and transcript downloads, mark as done, previous/next
  - **locked lessons**: the first 3 phrases and the offer
- Lesson 1 of each course is free with an account (Admin can raise it to 5).
- The member pages, the frame, sign-in and profile are in **English or Spanish** (EN/ES switch in the header; the
  first visit follows the browser's language).

**Admin** (`#admin/...`, English):
- **Overview**: revenue, buyers, waitlist, accounts, listeners and minutes this week, plus a setup checklist (audio, Stripe links, webhook secret).
- **Sales**: purchases, mark refunded / unlock again, give a course.
- **Waitlist**: CSV download.
- **Shop & setup**:
  - prices, currency, guarantee days and free lessons
  - six Payment Link boxes, each with its success address to paste in Stripe
  - the webhook address and secret status
  - lesson audio status, a public test address, and a "try lesson 1" button
- **Feedback**, **Users**, **Demo data** (five made-up listeners with purchases and listening days, plus waitlist emails).

## Setting it up in Anvil (once)

1. Anvil editor: **Create app → Clone from GitHub**, paste `https://github.com/arkulinskis/sayback`.
2. Check the **Users** service (email + password, Continue with Google, sign-up on) and the **App Secrets** service.
3. Accept the **Schema Mismatch** alert with **"The schema of the source code is correct"**.
4. Run it, sign up with arkulinskis@gmail.com first (that account becomes admin), then **Publish**.

## Before selling (Admin > Shop & setup shows the same checklist)

1. **Lesson audio.**
   - Cloudflare: R2 > Create bucket (private, e.g. `sayback-audio`), then R2 > Manage API tokens (Object Read & Write).
   - Upload: in `Documents/CLAUDE/sayback` run `python tools/upload_r2.py "r2://KEY:SECRET@ACCOUNT_ID/BUCKET"` (600 files, about 6.1 GB, resumable).
   - In the Anvil editor, add the App Secret `r2_url` with that same text.
2. **Stripe.**
   - Make one product and Payment Link per course and level (6). Set each link's "after payment" redirect to the address shown under its box, and paste the link into its box.
   - Add a webhook to `<app>/_/api/stripe` with the events `checkout.session.completed`, `checkout.session.async_payment_succeeded` and `charge.refunded`.
   - Put its signing secret in the App Secret `stripe_webhook_secret`.
3. Keep the prices on the page (Admin) and in Stripe the same.

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [Firebase Hosting](https://firebase.google.com/docs/hosting) | Outside web service | the sales pages' 90-second lesson previews (arkvital-media) |
| [Stripe Payment Links](https://stripe.com/payments/payment-links) | Outside web service | A ready-made Stripe checkout page for one product or price, shared as a link. |
| [Cloudflare R2](https://developers.cloudflare.com/r2/) | Outside web service | the 300 lesson MP3s and transcripts, played through 6-hour signed links |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Atkinson Hyperlegible, Bricolage Grotesque |
| [Anvil Uplink](https://anvil.works/docs/uplink) | Python package | Connects a Python program on any computer to an Anvil app, so each can call the other's functions. |

**Built into the browser:** Media Session API (lesson title on the lock screen and car display; play, pause, 10 s skips, next lesson), localStorage.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil JS bridge (anvil.js), Anvil Users, Anvil Google service, Anvil Secrets, Anvil Media.

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
                Layouts/Shell; Pages/ Landing, LandingEs, Auth, Library (#home), Lesson, Buy, Thanks, Profile, Admin
                Components/ RoadDemo (hero engine), Player (lesson player); Dialogs/Waitlist
                Items/ LessonTile, LevelChip, DayBar, PairRow, ProductCard, PurchaseRow, SaleRow, WaitRow, NavLink, ...
server_code/    Catalog.py (courses, access), Listening.py (library, lesson, progress, stats), Shop.py (prices, Stripe,
                webhook, waitlist, admin shop), Audio.py (R2 signed links), lessons_data.py (generated), DemoData.py,
                Accounts.py, Admin.py, Feedback.py, SchemaCheck.py, legal_server.py, common.py
theme/assets/   app.css, sb-road.js (hero), sb-player.js (player + car mode), sb-i18n.js (Spanish), sb-hero-data.js
                (generated), app-kit.js, theme.css (spinner), icons
tools/          make_catalog.py, make_landing_lists.py, make_hero.py, i18n_keys.py, i18n_es.py, check.py, ui_test.py + ui/,
                testing/ (server tests, audio_server.py = local stand-in for R2)
```
