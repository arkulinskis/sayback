/* Admin pages (local App Server only: signs up the ADMIN_EMAILS address, which becomes admin there).
   Runs FIRST (ui_test.py): points the lesson audio at tools/testing/audio_server.py, plays a lesson (admins hear
   everything), then visits every admin tab: sales + giving a course, waitlist, users, demo data. Resolves to {ok, log}. */
(async function () {
  const log = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const ok = (c, m) => { if (!c) throw new Error('FAILED: ' + m); log.push('ok   ' + m); };
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), hash);
    await sleep(300);
  }
  const btn = (scope, text) => Array.from((scope || document).querySelectorAll('button')).find((b) => b.textContent.trim().replace(/\s+/g, ' ') === text);
  try {
    window.SB.setLang('en');
    await page('#auth', () => $$('.au-card input').length >= 2);
    const inputs = () => $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter((i) => i.offsetParent);
    const pw = 'Hb-local-admin-Kq7-2026';
    type(inputs()[0], 'arkulinskis@gmail.com'); type(inputs()[1], pw);
    $$('.anvil-role-btn-block button').find((b) => /Sign in/.test(b.textContent)).click();
    await sleep(3000);
    if (location.hash !== '#home') {  // no account yet in this local database: create it
      $$('.ui-seg button').find((b) => /Create account/.test(b.textContent)).click();
      await sleep(500);
      const i = inputs(); type(i[0], 'Local Admin'); type(i[1], 'arkulinskis@gmail.com'); type(i[2], pw);
      const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
      $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    }
    await until(() => location.hash === '#home' && window.UI_READY, 'signed in as admin', 40000);

    // ---- Shop & setup: lesson audio from the local test server
    await page('#admin/shop', () => $('.ad-shop input'));
    const base = $$('.ad-shop input').find((i) => /r2\.dev/.test(i.placeholder || ''));
    type(base, 'http://127.0.0.1:8799');
    btn(document, 'Save').click();
    await until(() => /Test mode/.test($('.ad-shop').textContent), 'audio status says test mode');
    ok(/\/_\/api\/stripe/.test($('.anvil-role-ad-code').textContent), 'shop: shows the Stripe webhook address');
    ok(/#thanks\/es1/.test($('.ad-links').textContent), 'shop: shows each Payment Link\'s success address');
    ok(/Test mode/.test($('.ad-shop').textContent), 'shop: a test audio address can be saved');

    // ---- overview + setup checklist
    await page('#admin/overview', () => $$('.ad-stat').length >= 3 && $('.ad-check li.bad, .ad-check li.good'));
    ok(/\d/.test($('.ad-stat').textContent), 'overview: the numbers');
    ok(/0 of 6 set/.test($('.ad-setup').textContent) && $('.ad-check li.bad'), 'overview: setup checklist (no Stripe links yet)');

    // ---- an admin plays a Level 3 lesson (everything is open to admins)
    await page('#lesson/en-es/L3-05', () => $('.pl-play') && window.SB._player);
    const P = window.SB._player;
    $('.pl-play').click();
    await until(() => P.state().playing && P.state().position > 1.5, 'lesson audio plays', 30000);
    ok(/127\.0\.0\.1:8799\/en-es\/L3\/L3-05\.mp3/.test(P.state().src), 'lesson: plays from the storage address (' + P.state().src.slice(0, 50) + ')');
    const t0 = P.state().position;
    $('.pl-skip[data-act="fwd"]').click();
    await until(() => P.state().position > t0 + 8, '+10 s');
    ok(true, 'player: forward 10 seconds');
    P.seek(905); await sleep(800);
    ok(/Pep talk/.test($('.pl-chapter').textContent), 'player: chapter shows the 15-minute pep talk');
    P.seek(400); await sleep(600);
    $('.pl-car-btn').click();
    await until(() => !$('.pl-carmode').hidden && document.activeElement === $('.pl-car-play'), 'car mode opens');
    ok(true, 'car mode: full screen, focus on the big button');
    $('.pl-carmode .pl-car-play').click();
    await until(() => !P.state().playing, 'paused from car mode');
    $('.pl-car-exit').click();
    await until(() => $('.pl-carmode').hidden, 'car mode closes');
    ok(true, 'car mode: pause and exit');
    ok(/^https?:/.test($('.sb-files a').href) && $$('.anvil-role-sb-pairs .sb-pr').length === 20, 'lesson: downloads + 20 phrases');
    await page('#home/en-es/3', () => $$('.sb-tile').length === 30);
    await until(() => $$('.sb-tile.st-started').length >= 1, 'saved position shows', 15000);
    ok(true, 'library: the pause saved the position (tile shows how much was heard)');

    // ---- sales: give a course to an email without an account
    await page('#admin/sales', () => $('.ad-grant'));
    type($('.ad-grant input'), 'gift' + Date.now() + '@example.com');
    const sel = $('.ad-grant select');
    sel.selectedIndex = Array.from(sel.options).findIndex((o) => /Inglés · Levels 1-5/.test(o.textContent));
    sel.dispatchEvent(new Event('change', { bubbles: true }));
    btn($('.ad-grant'), 'Give it').click();
    await until(() => $$('.ad-sale').some((r) => /gift\d+@example\.com/.test(r.textContent)), 'gift listed');
    ok(true, 'sales: an admin gives a course to an email (it waits for the account)');
    ok($$('.ad-sale').length >= 2, 'sales: demo purchases listed');

    // ---- waitlist
    await page('#admin/waitlist', () => $('.ad-line'));
    ok($$('.ad-wait').length >= 1 && btn(document, 'Download CSV'), 'waitlist: entries + CSV button');

    // ---- the template's own admin checks
    await page('#admin/feedback', () => $('.ad-filter'));
    ok(/New \(\d+\)/.test($('.ad-filter').textContent), 'feedback: filter counts');
    await page('#admin/users', () => $$('.ad-user-row').length >= 1);
    const row = $$('.ad-user-row').find((r) => !/arkulinskis@gmail.com/.test(r.textContent));
    if (row) {
      const box = row.querySelectorAll('input[type=checkbox]')[1];
      const was = box.checked;
      box.click(); await sleep(2500); box.click(); await sleep(2500);
      ok(box.checked === was, 'users: Active switch saved twice (back as it was)');
    }
    type($('.anvil-role-ad-search-box'), 'nobody-matches-this'); $('.anvil-role-ic-search button').click();
    await until(() => $$('.ad-user-row').length === 0, 'search narrows');
    ok(/0 people/.test(document.body.textContent), 'users: search');
    await page('#admin/demo', () => $('.ad-demo'));
    ok(/Status:/.test($('.ad-demo').textContent), 'demo: status line');
    log.push('PASSED');
    return { ok: true, log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log };
  }
})();
