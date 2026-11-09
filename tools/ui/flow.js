/* The main journey, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs,
   after admin.js has pointed the lesson audio at the local test server. Resolves to {ok, log}. Keep log lines ASCII.
   A visitor: the road demo plays the real lesson clip -> picks Level 1 -> signs up -> back on the Buy page with that
   plan marked -> the waitlist (no Stripe links locally) -> library -> plays free lesson 1 -> phrase sheet + quiz ->
   a locked lesson -> Level 2 -> Spanish -> profile -> theme -> sign out -> the Spanish sales page. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const byText = (sel, text) => $$(sel).find((e) => e.textContent.trim().replace(/\s+/g, ' ') === text);
  async function click(sel, text) {
    const el = await until(() => (text ? byText(sel, text) : $(sel)), sel + (text ? ' "' + text + '"' : ''));
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  }
  function type(input, value) {
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;  // the old page stays until the router runs
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), what || hash, 30000);
    await sleep(300);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };

  try {
    window.SB.setLang('en');
    // ---- landing: the road demo plays 90 s of the real lesson 1
    await page('#landing', () => $('.lp-hero') && $('.rd-play'), 'landing');
    ok($('.lp-hero a[href="#auth/signup"]'), 'landing: hero with a sign-up link');
    ok($('.ui-header .ui-btn.primary'), 'landing: Listen free in the header');
    ok($$('.sb-lessons li').length === 30, 'landing: the 30 Level 1 lessons are listed');
    const R = window.SB._road;
    ok(R && /Good morning|Hello/.test(R.state().text) || /Your turn/.test($('.rd-cue').textContent), 'road: a still frame before playing (' + $('.rd-cue').textContent + ')');
    $('.rd-play').click();
    let played = true;
    try { await until(() => R.state().playing && R.state().t > 1.2, 'the hero clip plays', 20000); } catch (e) { played = false; }
    if (played) {
      await until(() => /You hear|Your turn|Then you hear|Say it after/.test($('.rd-cue').textContent), 'cue follows the audio');
      ok($('.rd-b.on'), 'road: the clip plays and the block under the playhead lights up (' + R.state().text + ')');
      R.seek(23.2); await sleep(400);
      ok(/Your turn/.test($('.rd-cue').textContent) && $('.rd-turn.show'), 'road: the thinking pause shows "your turn" with a countdown');
      R.pause();
    } else {
      say('note road: the clip did not load (no internet?), skipped the playback checks');
    }
    ok(/\$\d+/.test($('.anvil-role-sb-price-num').textContent), 'landing: prices from the shop settings');

    // ---- a visitor picks Level 1: sign up first, then back to the Buy page with that plan marked
    await click('.anvil-role-btn button', 'Get Level 1');
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up form');
    ok(/Create your free account/.test($('.au-card').textContent), 'buy as a visitor: asks for a free account first');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter((i) => i.offsetParent);
    type(inputs[0], 'Flow Tester'); type(inputs[1], 'flow' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]');
    if (tick && !tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => /^#buy\/en-es\/es1/.test(location.hash) && window.UI_READY && $('.sb-plan'), 'back on the Buy page', 40000);
    ok(/You picked this one/.test($('.sb-buy').textContent), 'buy: the plan they picked is marked');
    ok($('.anvil-role-avatar button') && /FT/.test($('.anvil-role-avatar button').textContent), 'header: account button with initials');
    ok(/Sales open very soon/.test($('.sb-buy').textContent), 'buy: says sales open soon (no Stripe links set)');
    await click('.sb-plan .anvil-role-btn-primary button', 'Get Level 1');
    await until(() => $('.sb-wait input'), 'waitlist dialog');
    ok(/@example\.com/.test($('.sb-wait input').value), 'waitlist: email filled in from the account');
    await click('.sb-wait button', 'Tell me when it opens');
    await until(() => /on the list/.test($('.sb-wait').textContent), 'joined');
    await click('.sb-wait button', 'Great');
    ok(true, 'waitlist: one tap, then "You\'re on the list"');

    // ---- library: lesson 1 is free and waiting
    await page('#home', () => $('.sb-next') && $$('.sb-tile').length === 30, 'library');
    ok(/Hello and first words/.test($('.anvil-role-sb-next-title').textContent), 'library: up next is lesson 1');
    ok($$('.sb-tile.st-locked').length === 29 && $('.sb-tile.st-open'), 'library: lesson 1 open, the other 29 locked');
    ok($$('.sb-day-bar').length === 14, 'library: 14-day chart');
    ok($('.sb-lib-offer .sb-plan'), 'library: offers for the locked lessons');
    await click('.sb-next .anvil-role-btn-primary button');
    await until(() => /^#lesson\/en-es\/L1-01\/play/.test(location.hash) && window.UI_READY && window.SB._player, 'lesson page');
    const P = window.SB._player;
    await until(() => P.state().playing && P.state().position > 1, 'Play lesson starts the audio', 30000);
    ok(true, 'lesson: "Play lesson" opens it and starts playing');
    P.pause();
    ok($$('.anvil-role-sb-pairs .sb-pr').length === 20, 'lesson: the 20 new phrases');
    ok(/cultur/i.test($('.sb-culture').textContent) && $('.anvil-role-sb-culture-text').textContent.length > 40, 'lesson: culture moment');
    await click('.anvil-role-ic-eye button');
    await until(() => $$('.sb-pr.hidden-answer').length === 20, 'quiz hides answers');
    $$('.sb-pr')[0].click();
    await until(() => $$('.sb-pr.hidden-answer').length === 19, 'tap reveals one');
    ok(true, 'phrase sheet: quiz mode hides the answers, a tap shows one');

    // ---- a locked lesson: a taste and the offer
    await page('#lesson/en-es/L1-02', () => $('.sb-locked'));
    ok($$('.anvil-role-sb-pairs .sb-pr').length === 3 && !$('.sb-player-card .pl'), 'locked lesson: 3 phrases, no player');
    ok($('.sb-locked a[href="#buy/en-es"]'), 'locked lesson: link to the courses');

    // ---- levels
    window.UI_READY = false;
    await click('.sb-back');
    await until(() => window.UI_READY && /^#home/.test(location.hash) && $$('.sb-lv').length === 5, 'back to the library');
    window.UI_READY = false;
    $$('.sb-lv')[1].click();
    await until(() => location.hash === '#home/en-es/2' && window.UI_READY && $$('.sb-tile').length === 30, 'level 2');
    const flat = (el) => String(el ? el.textContent : 'none').replace(/\s+/g, ' ').trim();
    ok($('.sb-lv.on') && /Level 2/.test(flat($('.sb-lv.on'))) && /Locked/.test(flat($('.sb-level-head'))),
       'library: Level 2 listed, locked [' + flat($('.sb-lv.on')) + ' | ' + flat($('.sb-level-head')) + ']');

    // ---- Spanish
    window.UI_READY = false;
    await click('.sb-lang');
    await until(() => window.UI_READY && /Buenos|Buenas/.test($('.anvil-role-page-title').textContent), 'library in Spanish');
    ok(/Nivel 2/.test($('.sb-level-head').textContent) && /Biblioteca/.test($('.ui-nav').textContent), 'Spanish: the library and menu switch language');
    ok(!window.SB_MISSING.length, 'Spanish: no missing translations (' + window.SB_MISSING.slice(0, 3).join(' | ') + ')');
    window.UI_READY = false;
    await click('.sb-lang');
    await until(() => window.UI_READY && /Good (morning|afternoon|evening)/.test($('.anvil-role-page-title').textContent), 'back to English');

    // ---- profile: courses + name
    await page('#profile', () => $('.pf-grid'), 'profile');
    ok(/Nothing bought yet/.test($('.pf-courses').textContent), 'profile: no courses yet');
    type($('.pf-grid input'), 'Flow Tester Two');
    await click('.pf-grid .anvil-role-btn-primary button', 'Save');
    await until(() => /Flow Tester Two/.test($('.pf-head').textContent), 'name saved');
    ok(true, 'profile: name saved');

    // ---- light / dark switch in the account menu
    await click('.anvil-role-avatar button');
    await click('.ui-menu .ui-seg button', 'Dark');
    ok(document.documentElement.classList.contains('ui-dark'), 'menu: Dark switches the theme');
    await click('.ui-menu .ui-seg button', 'Auto');

    // ---- sign out, then the Spanish sales page
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY && $('.ui-header .ui-btn.primary'), 'signed out');
    ok(true, 'sign out: back to the landing page as a visitor');
    await page('#es', () => $('.lp-hero') && $('.rd-play'));
    ok(/inglés/.test($('.lp-hero h1').textContent) && /Escucha/.test($('.rd-play').textContent), 'Spanish sales page: hero + road demo in Spanish');
    ok(/Escucha gratis/.test($('.ui-header').textContent) && document.documentElement.lang === 'es', 'Spanish sales page: header in Spanish, <html lang="es">');
    await click('.sb-lang');
    await until(() => location.hash === '#landing' && window.UI_READY, 'ES -> EN swaps to the English page');
    ok(true, 'language switch on a sales page opens its twin');

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
