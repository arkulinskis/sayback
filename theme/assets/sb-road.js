/* Sayback landing hero: 90 seconds of the real lesson 1 plays while its phrases drive past on a road.
   Blocks = what you hear (prompt), your turn (the thinking pause, with a countdown), the answer, and "say it after
   the voice" for new phrases. Timings come from tools/make_hero.py (window.SB_HERO).
     SB.road(el, {course: 'en-es', labels: {...}, onEnd}) -> {play, pause, state, destroy}
   Content is visible without playing (a still frame), and the road doesn't glide under reduced motion. */
(function () {
  var SB = window.SB = window.SB || {};
  var PX = 120;  // pixels per second of audio (short phrases still fit their block)
  var MIC = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg>';
  var REP = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 13.7-5.6L20 9"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-13.7 5.6L4 15"/><path d="M4 20v-5h5"/></svg>';
  var PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z" fill="currentColor"/></svg>';
  var PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/><rect x="13.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/></svg>';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function fmt(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }

  SB.road = function (el, o) {
    o = o || {};
    var data = (window.SB_HERO || {})[o.course || 'en-es'];
    if (!data || !el) return null;
    var L = Object.assign({ play: 'Hear 90 seconds of lesson 1', pause: 'Pause', again: 'Hear it again',
      listen: 'You hear', say: 'Your turn: say it out loud', repeat: 'Say it after the voice', answer: 'Then you hear',
      failed: "The sample didn't load. Check your connection and try again." }, o.labels || {});
    var parts = data.parts;
    var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var idle = (parts.filter(function (p) { return p[2] === 'say'; })[0] || parts[0])[0] + 1.1;
    var audio = new Audio();
    audio.preload = 'none';
    audio.src = data.src;
    var raf = 0, dead = false, lastIndex = -2, started = false;

    var blocks = parts.map(function (p, i) {
      var kind = p[2], w = Math.max(10, (p[1] - p[0]) * PX - 4);
      var inner = kind === 'say' ? MIC : (kind === 'rep' ? REP : '<span>' + esc(p[3]) + '</span>');
      return '<div class="rd-b rd-' + kind + '" data-i="' + i + '" style="left:' + (p[0] * PX).toFixed(1) + 'px;width:' + w.toFixed(1) + 'px">' + inner + '</div>';
    }).join('');
    el.innerHTML =
      '<div class="rd">' +
      '  <div class="rd-stage" aria-hidden="true">' +
      '    <div class="rd-cue"></div>' +
      '    <div class="rd-line"><span class="rd-text"></span></div>' +
      '    <div class="rd-turn"><svg viewBox="0 0 40 40"><circle class="rd-ring-bg" cx="20" cy="20" r="17"/><circle class="rd-ring" cx="20" cy="20" r="17"/></svg><span class="rd-count"></span></div>' +
      '  </div>' +
      '  <div class="rd-road" aria-hidden="true"><div class="rd-lane rd-enter">' + blocks + '</div><div class="rd-head"></div></div>' +
      '  <div class="rd-bar">' +
      '    <button type="button" class="rd-play">' + PLAY + PAUSE + '<span class="rd-play-text">' + esc(L.play) + '</span></button>' +
      '    <span class="rd-time">' + fmt(data.length) + '</span>' +
      '  </div>' +
      '  <p class="rd-fail" role="status"></p>' +
      '</div>';
    var root = el.querySelector('.rd'), lane = el.querySelector('.rd-lane'), road = el.querySelector('.rd-road');
    var cue = el.querySelector('.rd-cue'), text = el.querySelector('.rd-text'), turn = el.querySelector('.rd-turn');
    var ring = el.querySelector('.rd-ring'), count = el.querySelector('.rd-count'), btn = el.querySelector('.rd-play');
    var btnText = el.querySelector('.rd-play-text'), timeEl = el.querySelector('.rd-time'), fail = el.querySelector('.rd-fail');
    var nodes = Array.prototype.slice.call(lane.children);
    var C = 2 * Math.PI * 17;
    ring.style.strokeDasharray = C.toFixed(2);

    function at(t) {
      for (var i = 0; i < parts.length; i++) { if (t < parts[i][1]) return t >= parts[i][0] ? i : -1 - i; }
      return -1 - parts.length;
    }
    function itemPrompt(i) {   // the prompt that this answer / pause belongs to
      for (var j = i; j >= 0; j--) if (parts[j][2] === 'p') return parts[j][3];
      return '';
    }
    function render(t) {
      var x = road.clientWidth * 0.32 - t * PX;
      if (!reduced) lane.style.transform = 'translateX(' + x.toFixed(1) + 'px)';
      var i = at(t), idx = i >= 0 ? i : (-1 - i < parts.length ? -1 - i : parts.length - 1);
      var p = parts[idx], live = i >= 0;
      if (reduced && idx !== lastIndex) lane.style.transform = 'translateX(' + (road.clientWidth * 0.32 - p[0] * PX).toFixed(1) + 'px)';
      if (idx !== lastIndex) {
        nodes.forEach(function (n, k) { n.classList.toggle('on', k === idx); n.classList.toggle('past', k < idx); });
        var kind = p[2];
        root.setAttribute('data-kind', kind);
        cue.textContent = kind === 'p' ? L.listen : kind === 'say' ? L.say : kind === 'rep' ? L.repeat : L.answer;
        text.textContent = kind === 'say' ? itemPrompt(idx) : p[3];
        text.className = 'rd-text rd-t-' + kind;
        lastIndex = idx;
      }
      root.classList.toggle('rd-gap', !live);
      var timed = p[2] === 'say' || p[2] === 'rep';
      turn.classList.toggle('show', timed);
      if (timed) {
        var left = Math.max(0, p[1] - Math.max(t, p[0])), whole = p[1] - p[0];
        ring.style.strokeDashoffset = (C * (1 - left / whole)).toFixed(2);
        count.textContent = Math.ceil(left);
      }
      timeEl.textContent = fmt(started ? data.length - t : data.length);
    }
    function loop() {
      if (dead) return;
      render(audio.currentTime || 0);
      if (!audio.paused) raf = requestAnimationFrame(loop);
    }
    function setBtn() {
      var on = !audio.paused;
      root.classList.toggle('is-playing', on);
      btnText.textContent = on ? L.pause : (audio.ended ? L.again : L.play);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    audio.addEventListener('play', function () { started = true; fail.textContent = ''; setBtn(); cancelAnimationFrame(raf); raf = requestAnimationFrame(loop); });
    audio.addEventListener('pause', setBtn);
    audio.addEventListener('ended', function () { setBtn(); if (o.onEnd) o.onEnd(); });
    audio.addEventListener('error', function () { if (!dead) { fail.textContent = L.failed; setBtn(); } });
    btn.addEventListener('click', function () {
      if (audio.paused) {
        if (audio.ended || !started) { audio.currentTime = 0; }
        var pr = audio.play();
        if (pr && pr.catch) pr.catch(function () { fail.textContent = L.failed; });
      } else audio.pause();
    });
    window.addEventListener('resize', onResize);
    function onResize() { lastIndex = -2; render(started ? audio.currentTime : idle); }
    render(idle);
    requestAnimationFrame(function () { lane.classList.remove('rd-enter'); });

    return SB._road = {
      play: function () { btn.click(); },
      pause: function () { audio.pause(); },
      state: function () { return { playing: !audio.paused, t: audio.currentTime, kind: root.getAttribute('data-kind'), text: text.textContent, src: audio.src }; },
      seek: function (t) { started = true; audio.currentTime = t; lastIndex = -2; render(t); },
      destroy: function () {
        dead = true;
        cancelAnimationFrame(raf);
        audio.pause();
        audio.removeAttribute('src');
        window.removeEventListener('resize', onResize);
        el.innerHTML = '';
      }
    };
  };
})();
