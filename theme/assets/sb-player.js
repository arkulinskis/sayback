/* Sayback lesson player: one <audio>, big controls, a scrubber with the lesson's chapter marks, lock-screen and car
   controls (Media Session), a full-screen car mode, and progress reports for the server.
   Wrapped by client_code/Components/Player. Python passes plain values and callbacks:
     SB.player(el, {src, start, title, album, marks: [firstPhrase, pep1, pep2, outro], labels: {...},
                    trip (minutes, 0 = whole lesson), think (extra seconds after each prompt), cues ("3 base-36 digits
                    per cue, deciseconds"), onTick(position, listenedSeconds, done), onEnd(), onError(wantedToPlay),
                    onNext(), onState(playing), onStop(nextPart)})
   returns {play, pause, toggle, seek, skip, car(on), speed(x), trip(min), think(sec), swap(src, at, play), state(),
            destroy}.
   Trip: playing with a trip length stops at the pep talk that best fits it (the first pep-talk mark after
   start + minutes - 2 min), seeks back to the mark so the next trip opens with that pep talk, and calls onStop.
   Thinking time: crossing a cue (the end of a recall prompt, media time) holds the audio for `think` seconds while a
   ring fills, then the recorded gap plays as usual. Seeks never trigger a hold. */
(function () {
  var SB = window.SB = window.SB || {};
  var TICK = 20;                  // seconds of listening between saves
  var ICON = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z" fill="currentColor"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/><rect x="13.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/></svg>',
    back: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>',
    fwd: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/></svg>',
    ring: '<svg class="pl-ring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="47" pathLength="100"/></svg>'
  };
  function fmt(s) {
    s = Math.max(0, Math.round(s || 0));
    return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function decodeCues(s) {
    var out = [];
    s = String(s || '');
    for (var i = 0; i + 3 <= s.length; i += 3) {
      var v = parseInt(s.substr(i, 3), 36);
      if (!isNaN(v)) out.push(v / 10);
    }
    return out;
  }
  SB.decodeCues = decodeCues;

  SB.player = function (el, o) {
    o = o || {};
    var L = Object.assign({
      play: 'Play', pause: 'Pause', back: 'Back 10 seconds', fwd: 'Forward 10 seconds', position: 'Position in the lesson',
      intro: 'Intro', part: 'Part {n} of 3', pep: 'Pep talk', outro: 'Wrap-up', car: 'Car mode', exit: 'Exit car mode',
      speed: 'Speed', carHint: 'Tap anywhere big to play or pause. Eyes on the road.', turn: 'Your turn: say it out loud',
      partNext: 'Part {n} next'
    }, o.labels || {});
    var marks = (o.marks && o.marks.length === 4) ? o.marks : [75, 900, 1800, 2670];
    var dur = 2700, listened = 0, sinceTick = 0, lastT = null, playing = false, dead = false, rate = 1, ended = false;
    var startAt = +o.start || 0, firstLoad = true, autoPlay = false, wantPlay = false, lastPos = startAt;
    var tripMin = +o.trip || 0, stopAt = null;
    var cues = decodeCues(o.cues), thinkSec = +o.think || 0, holding = false, holdTimer = null, checkT = null, seekAt = 0, poll = null;
    var wake = null;
    var audio = new Audio();
    audio.preload = 'metadata';
    audio.src = o.src || '';

    el.innerHTML =
      '<div class="pl">' +
      '  <div class="pl-main">' +
      '    <button type="button" class="pl-skip" data-act="back" aria-label="' + esc(L.back) + '">' + ICON.back + '<span>10</span></button>' +
      '    <span class="pl-playwrap">' + ICON.ring + '<button type="button" class="pl-play" data-act="toggle" aria-label="' + esc(L.play) + '">' + ICON.play + ICON.pause + '</button></span>' +
      '    <button type="button" class="pl-skip" data-act="fwd" aria-label="' + esc(L.fwd) + '">' + ICON.fwd + '<span>10</span></button>' +
      '  </div>' +
      '  <div class="pl-bar">' +
      '    <div class="pl-track" aria-hidden="true"><i class="pl-fill"></i><i class="pl-stop" hidden></i>' +
      marks.map(function (m, i) { return '<b class="pl-mark pl-mark-' + i + '" style="left:' + (m / dur * 100).toFixed(2) + '%"></b>'; }).join('') +
      '    </div>' +
      '    <input type="range" class="pl-range" min="0" max="' + dur + '" step="1" value="0" aria-label="' + esc(L.position) + '">' +
      '  </div>' +
      '  <div class="pl-times"><span class="pl-now">0:00</span><span class="pl-chapter"></span><span class="pl-left">-45:00</span></div>' +
      '  <div class="pl-extra">' +
      '    <button type="button" class="pl-chip" data-act="speed" aria-label="' + esc(L.speed) + '">1×</button>' +
      '    <button type="button" class="pl-chip pl-car-btn" data-act="car">' + esc(L.car) + '</button>' +
      '  </div>' +
      '</div>';
    var root = el.querySelector('.pl'), playBtn = el.querySelector('.pl-play'), range = el.querySelector('.pl-range');
    var fill = el.querySelector('.pl-fill'), nowEl = el.querySelector('.pl-now'), leftEl = el.querySelector('.pl-left');
    var chapEl = el.querySelector('.pl-chapter'), speedBtn = el.querySelector('[data-act="speed"]'), stopEl = el.querySelector('.pl-stop');

    var car = document.createElement('div');
    car.className = 'pl-carmode';
    car.setAttribute('role', 'dialog');
    car.setAttribute('aria-modal', 'true');
    car.setAttribute('aria-label', L.car);
    car.innerHTML =
      '<div class="pl-car-top"><div><div class="pl-car-album">' + esc(o.album || '') + '</div><div class="pl-car-title">' + esc(o.title || '') + '</div></div>' +
      '<button type="button" class="pl-car-exit" data-act="exit">' + esc(L.exit) + '</button></div>' +
      '<span class="pl-car-playwrap">' + ICON.ring + '<button type="button" class="pl-car-play" data-act="toggle" aria-label="' + esc(L.play) + '">' + ICON.play + ICON.pause + '</button></span>' +
      '<div class="pl-car-row"><button type="button" class="pl-car-skip" data-act="back" aria-label="' + esc(L.back) + '">' + ICON.back + '<span>10</span></button>' +
      '<div class="pl-car-time"><span class="pl-car-now">0:00</span><span class="pl-car-chap"></span></div>' +
      '<button type="button" class="pl-car-skip" data-act="fwd" aria-label="' + esc(L.fwd) + '">' + ICON.fwd + '<span>10</span></button></div>' +
      '<p class="pl-car-hint">' + esc(L.carHint) + '</p>';
    car.hidden = true;
    document.body.appendChild(car);

    function pos() { var t = audio.currentTime || 0; return t > 0 ? t : lastPos; }
    function chapter(t) {
      if (holding) return L.turn;
      if (t < marks[0]) return L.intro;
      if (t >= marks[3]) return L.outro;
      if ((t >= marks[1] && t < marks[1] + 12) || (t >= marks[2] && t < marks[2] + 12)) return L.pep;
      return L.part.replace('{n}', t < marks[1] ? 1 : (t < marks[2] ? 2 : 3));
    }
    function draw() {
      var t = audio.currentTime || 0;
      if (t > 0) lastPos = t;
      var d = isFinite(audio.duration) && audio.duration > 0 ? audio.duration : dur;
      if (document.activeElement !== range) range.value = Math.round(t);
      range.max = Math.round(d);
      range.setAttribute('aria-valuetext', fmt(t) + ' / ' + fmt(d));
      fill.style.transform = 'scaleX(' + Math.min(1, t / d).toFixed(4) + ')';
      stopEl.hidden = stopAt === null;
      if (stopAt !== null) stopEl.style.left = (stopAt / d * 100).toFixed(2) + '%';
      nowEl.textContent = fmt(t);
      leftEl.textContent = '-' + fmt(d - t);
      var ch = chapter(t);
      chapEl.textContent = ch;
      car.querySelector('.pl-car-now').textContent = fmt(t) + ' / ' + fmt(d);
      car.querySelector('.pl-car-chap').textContent = ch;
    }
    function setMeta(prefix) {
      if (!('mediaSession' in navigator)) return;
      try {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: (prefix ? prefix + ' · ' : '') + (o.title || 'Sayback'), artist: 'Sayback', album: o.album || '',
          artwork: [{ src: '_/theme/icon-512.png', sizes: '512x512', type: 'image/png' }]
        });
      } catch (e) {}
    }
    function setPlaying(p) {
      playing = p;
      root.classList.toggle('is-playing', p);
      car.classList.toggle('is-playing', p);
      [playBtn, car.querySelector('.pl-car-play')].forEach(function (b) { b.setAttribute('aria-label', p ? L.pause : L.play); });
      if ('mediaSession' in navigator) navigator.mediaSession.playbackState = p ? 'playing' : 'paused';
      if (p && !poll) poll = setInterval(checkCue, 100);
      if (!p && poll) { clearInterval(poll); poll = null; }
      if (o.onState) o.onState(p);
    }
    function report(done) {
      var heard = Math.round(listened);
      listened = 0;
      sinceTick = 0;
      if (o.onTick) o.onTick(Math.round(pos()), heard, !!done);
    }
    function resume() { var p = audio.play(); if (p && p.catch) p.catch(function () {}); }

    /* ---- trip length: stop at a pep talk ---- */
    function planStop() {
      stopAt = null;
      if (tripMin > 0) {
        var start = audio.currentTime || 0, target = start + tripMin * 60 - 120;
        for (var k = 1; k <= 2; k++) {
          if (marks[k] > target && marks[k] > start + 30) { stopAt = marks[k]; break; }
        }
      }
      draw();
    }
    function doStop() {
      var at = stopAt, part = at >= marks[2] - 3 ? 3 : 2;
      stopAt = null;
      audio.pause();                    // the pause event (async) reports the position: the mark, set just below
      audio.currentTime = at;
      lastT = at;
      lastPos = at;
      setMeta(L.partNext.replace('{n}', part));
      draw();
      if (o.onStop) o.onStop(part);
    }

    /* ---- thinking time: hold after each prompt ---- */
    function setThinking(on) {
      [root, car].forEach(function (x) {
        x.style.setProperty('--think', thinkSec + 's');
        x.classList.toggle('is-thinking', on);
      });
    }
    function clearHold() {
      if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
      if (holding) { holding = false; setThinking(false); }
    }
    function hold() {
      holding = true;
      audio.pause();                    // the pause handler ignores it: to the listener this is still playing
      setThinking(true);
      draw();
      var secs = thinkSec;
      holdTimer = setTimeout(function () {
        holdTimer = null;
        if (!holding || dead) return;
        holding = false;
        setThinking(false);
        listened += secs; sinceTick += secs;   // thinking out loud is practice time too
        checkT = audio.currentTime;
        var p = audio.play();
        if (p && p.catch) p.catch(function () { setPlaying(false); report(false); });
        draw();
      }, secs * 1000);
    }
    function checkCue() {
      var t = audio.currentTime || 0, prev = checkT;
      checkT = t;
      if (!playing || holding || !thinkSec || !cues.length || audio.paused || audio.seeking) return;
      if (prev === null || t <= prev || t - prev > 1.5 || Date.now() - seekAt < 700) return;
      var lo = 0, hi = cues.length;       // first cue after prev
      while (lo < hi) { var mid = (lo + hi) >> 1; if (cues[mid] <= prev) lo = mid + 1; else hi = mid; }
      if (lo < cues.length && cues[lo] <= t) hold();
    }
    function noteSeek() { seekAt = Date.now(); checkT = audio.currentTime || 0; }

    function onTime() {
      var t = audio.currentTime;
      if (lastT !== null && playing && !holding) {
        var dt = t - lastT;
        if (dt > 0 && dt < 2.5) { listened += dt / rate; sinceTick += dt / rate; }
      }
      lastT = t;
      if (stopAt !== null && playing && !holding && t >= stopAt) { doStop(); return; }
      checkCue();
      if (sinceTick >= TICK) report(false);
      draw();
    }
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', function () {
      var s = startAt, d = audio.duration || dur;
      if (s > (firstLoad ? 5 : 1) && s < d - (firstLoad ? 30 : 2)) audio.currentTime = s;
      firstLoad = false;
      lastT = audio.currentTime;
      noteSeek();
      draw();
      if (autoPlay) { autoPlay = false; resume(); }
    });
    audio.addEventListener('play', function () { ended = false; setPlaying(true); });
    audio.addEventListener('playing', function () { wantPlay = false; });
    audio.addEventListener('pause', function () { if (holding) return; setPlaying(false); if (!ended && !dead) report(false); });
    audio.addEventListener('seeking', noteSeek);
    audio.addEventListener('ended', function () { clearHold(); ended = true; setPlaying(false); report(true); if (o.onEnd) o.onEnd(); });
    audio.addEventListener('error', function () {
      if (dead || !audio.src) return;
      var want = playing || wantPlay;
      wantPlay = false;
      clearHold();
      if (playing) setPlaying(false);
      if (o.onError) o.onError(want);
    });

    function act(name) {
      if (name === 'toggle') api.toggle();
      else if (name === 'back') api.skip(-10);
      else if (name === 'fwd') api.skip(10);
      else if (name === 'car') api.car(true);
      else if (name === 'exit') api.car(false);
      else if (name === 'speed') api.speed(rate === 1 ? 0.85 : (rate < 1 ? 1.15 : 1));
    }
    function onClick(e) {
      var b = e.target.closest('[data-act]');
      if (b) { e.preventDefault(); act(b.getAttribute('data-act')); }
    }
    root.addEventListener('click', onClick);
    car.addEventListener('click', onClick);
    range.addEventListener('input', function () { api.seek(+range.value); });
    function onKey(e) { if (e.key === 'Escape' && !car.hidden) api.car(false); }
    document.addEventListener('keydown', onKey);
    function keepScreenOn() {
      // car mode keeps the screen awake, so thinking time and the big buttons work without unlocking the phone
      if (car.hidden || wake || !navigator.wakeLock || document.visibilityState !== 'visible') return;
      navigator.wakeLock.request('screen').then(function (w) {
        wake = w;
        w.addEventListener('release', function () { wake = null; });
      }).catch(function () {});
    }
    document.addEventListener('visibilitychange', keepScreenOn);

    if ('mediaSession' in navigator) {
      try {
        setMeta('');
        var ms = navigator.mediaSession;
        ms.setActionHandler('play', function () { api.play(); });
        ms.setActionHandler('pause', function () { api.pause(); });
        ms.setActionHandler('seekbackward', function () { api.skip(-10); });
        ms.setActionHandler('seekforward', function () { api.skip(10); });
        ms.setActionHandler('nexttrack', o.onNext ? function () { o.onNext(); } : null);
      } catch (e) {}
    }
    draw();

    var api = {
      play: function () {
        if (holding) { clearHold(); resume(); return; }
        wantPlay = true;
        setMeta('');
        planStop();
        resume();
      },
      pause: function () {
        if (holding) { clearHold(); setPlaying(false); report(false); return; }
        audio.pause();
      },
      toggle: function () { if (holding || !audio.paused) api.pause(); else api.play(); },
      seek: function (t) {
        var wasHolding = holding;
        clearHold();
        noteSeek();
        audio.currentTime = Math.max(0, t);
        lastT = audio.currentTime;
        if (stopAt !== null && audio.currentTime >= stopAt - 1) planStop();   // jumped past the stop: aim for the next one
        if (wasHolding) resume();
        draw();
      },
      skip: function (d) { api.seek((audio.currentTime || 0) + d); },
      speed: function (x) { rate = x; audio.playbackRate = x; speedBtn.textContent = (x === 1 ? '1' : String(x)) + '×'; },
      trip: function (m) { tripMin = +m || 0; if (playing) planStop(); else { stopAt = null; draw(); } },
      think: function (s) { thinkSec = +s || 0; if (!thinkSec && holding) { clearHold(); resume(); } },
      swap: function (src, at, play) {
        // a fresh signed link (the old one expired): same place, same speed, playing again if it was
        clearHold();
        startAt = +at || 0;
        lastPos = startAt;
        autoPlay = !!play;
        audio.src = src;
        audio.load();
        audio.playbackRate = rate;
      },
      car: function (on) {
        car.hidden = !on;
        document.documentElement.classList.toggle('pl-car-open', !!on);
        if (on) { car.querySelector('.pl-car-play').focus(); keepScreenOn(); }
        else { playBtn.focus(); if (wake) { try { wake.release(); } catch (e) {} wake = null; } }
      },
      state: function () {
        return { playing: playing, position: pos(), duration: audio.duration || dur, car: !car.hidden, rate: rate,
                 src: audio.currentSrc || audio.src, holding: holding, stopAt: stopAt, trip: tripMin, think: thinkSec,
                 cues: cues.length };
      },
      destroy: function () {
        if (dead) return;
        if (playing) report(false);
        clearHold();
        if (poll) { clearInterval(poll); poll = null; }
        dead = true;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
        document.removeEventListener('keydown', onKey);
        document.removeEventListener('visibilitychange', keepScreenOn);
        if (wake) { try { wake.release(); } catch (e) {} wake = null; }
        document.documentElement.classList.remove('pl-car-open');
        if (car.parentNode) car.parentNode.removeChild(car);
        if ('mediaSession' in navigator) {
          ['play', 'pause', 'seekbackward', 'seekforward', 'nexttrack'].forEach(function (a) { try { navigator.mediaSession.setActionHandler(a, null); } catch (e) {} });
        }
        el.innerHTML = '';
      },
      _audio: audio,
      _cues: cues
    };
    SB._player = api;  // tests drive the last player through this
    return api;
  };
})();
