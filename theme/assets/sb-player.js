/* Sayback lesson player: one <audio>, big controls, a scrubber with the lesson's chapter marks, lock-screen and car
   controls (Media Session), a full-screen car mode, and progress reports for the server.
   Wrapped by client_code/Components/Player. Python passes plain values and callbacks:
     SB.player(el, {src, start, title, album, marks: [firstPhrase, pep1, pep2, outro], labels: {...},
                    onTick(position, listenedSeconds, done), onEnd(), onError(), onNext(), onState(playing)})
   returns {play, pause, toggle, seek, skip, car(on), speed(x), state(), destroy}. */
(function () {
  var SB = window.SB = window.SB || {};
  var TICK = 20;                  // seconds of listening between saves
  var ICON = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z" fill="currentColor"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/><rect x="13.5" y="5" width="4" height="14" rx="1.2" fill="currentColor"/></svg>',
    back: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>',
    fwd: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/></svg>'
  };
  function fmt(s) {
    s = Math.max(0, Math.round(s || 0));
    return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  SB.player = function (el, o) {
    o = o || {};
    var L = Object.assign({
      play: 'Play', pause: 'Pause', back: 'Back 10 seconds', fwd: 'Forward 10 seconds', position: 'Position in the lesson',
      intro: 'Intro', part: 'Part {n} of 3', pep: 'Pep talk', outro: 'Wrap-up', car: 'Car mode', exit: 'Exit car mode',
      speed: 'Speed', carHint: 'Tap anywhere big to play or pause. Eyes on the road.'
    }, o.labels || {});
    var marks = (o.marks && o.marks.length === 4) ? o.marks : [75, 900, 1800, 2670];
    var dur = 2700, listened = 0, sinceTick = 0, lastT = null, playing = false, dead = false, rate = 1, ended = false;
    var audio = new Audio();
    audio.preload = 'metadata';
    audio.src = o.src || '';

    el.innerHTML =
      '<div class="pl">' +
      '  <div class="pl-main">' +
      '    <button type="button" class="pl-skip" data-act="back" aria-label="' + esc(L.back) + '">' + ICON.back + '<span>10</span></button>' +
      '    <button type="button" class="pl-play" data-act="toggle" aria-label="' + esc(L.play) + '">' + ICON.play + ICON.pause + '</button>' +
      '    <button type="button" class="pl-skip" data-act="fwd" aria-label="' + esc(L.fwd) + '">' + ICON.fwd + '<span>10</span></button>' +
      '  </div>' +
      '  <div class="pl-bar">' +
      '    <div class="pl-track" aria-hidden="true"><i class="pl-fill"></i>' +
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
    var chapEl = el.querySelector('.pl-chapter'), speedBtn = el.querySelector('[data-act="speed"]');

    var car = document.createElement('div');
    car.className = 'pl-carmode';
    car.setAttribute('role', 'dialog');
    car.setAttribute('aria-modal', 'true');
    car.setAttribute('aria-label', L.car);
    car.innerHTML =
      '<div class="pl-car-top"><div><div class="pl-car-album">' + esc(o.album || '') + '</div><div class="pl-car-title">' + esc(o.title || '') + '</div></div>' +
      '<button type="button" class="pl-car-exit" data-act="exit">' + esc(L.exit) + '</button></div>' +
      '<button type="button" class="pl-car-play" data-act="toggle" aria-label="' + esc(L.play) + '">' + ICON.play + ICON.pause + '</button>' +
      '<div class="pl-car-row"><button type="button" class="pl-car-skip" data-act="back" aria-label="' + esc(L.back) + '">' + ICON.back + '<span>10</span></button>' +
      '<div class="pl-car-time"><span class="pl-car-now">0:00</span><span class="pl-car-chap"></span></div>' +
      '<button type="button" class="pl-car-skip" data-act="fwd" aria-label="' + esc(L.fwd) + '">' + ICON.fwd + '<span>10</span></button></div>' +
      '<p class="pl-car-hint">' + esc(L.carHint) + '</p>';
    car.hidden = true;
    document.body.appendChild(car);

    function chapter(t) {
      if (t < marks[0]) return L.intro;
      if (t >= marks[3]) return L.outro;
      if ((t >= marks[1] && t < marks[1] + 12) || (t >= marks[2] && t < marks[2] + 12)) return L.pep;
      return L.part.replace('{n}', t < marks[1] ? 1 : (t < marks[2] ? 2 : 3));
    }
    function draw() {
      var t = audio.currentTime || 0;
      var d = isFinite(audio.duration) && audio.duration > 0 ? audio.duration : dur;
      if (document.activeElement !== range) range.value = Math.round(t);
      range.max = Math.round(d);
      range.setAttribute('aria-valuetext', fmt(t) + ' / ' + fmt(d));
      fill.style.transform = 'scaleX(' + Math.min(1, t / d).toFixed(4) + ')';
      nowEl.textContent = fmt(t);
      leftEl.textContent = '-' + fmt(d - t);
      var ch = chapter(t);
      chapEl.textContent = ch;
      car.querySelector('.pl-car-now').textContent = fmt(t) + ' / ' + fmt(d);
      car.querySelector('.pl-car-chap').textContent = ch;
    }
    function setPlaying(p) {
      playing = p;
      root.classList.toggle('is-playing', p);
      car.classList.toggle('is-playing', p);
      [playBtn, car.querySelector('.pl-car-play')].forEach(function (b) { b.setAttribute('aria-label', p ? L.pause : L.play); });
      if ('mediaSession' in navigator) navigator.mediaSession.playbackState = p ? 'playing' : 'paused';
      if (o.onState) o.onState(p);
    }
    function report(done) {
      var heard = Math.round(listened);
      listened = 0;
      sinceTick = 0;
      if (o.onTick) o.onTick(Math.round(audio.currentTime || 0), heard, !!done);
    }

    function onTime() {
      var t = audio.currentTime;
      if (lastT !== null && playing) {
        var dt = t - lastT;
        if (dt > 0 && dt < 2.5) { listened += dt / rate; sinceTick += dt / rate; }
      }
      lastT = t;
      if (sinceTick >= TICK) report(false);
      draw();
    }
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', function () {
      var s = +o.start || 0;
      if (s > 5 && s < (audio.duration || dur) - 30) audio.currentTime = s;
      lastT = audio.currentTime;
      draw();
    });
    audio.addEventListener('play', function () { ended = false; setPlaying(true); });
    audio.addEventListener('pause', function () { setPlaying(false); if (!ended && !dead) report(false); });
    audio.addEventListener('ended', function () { ended = true; setPlaying(false); report(true); if (o.onEnd) o.onEnd(); });
    audio.addEventListener('error', function () { if (!dead && audio.src && o.onError) o.onError(); });

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
    range.addEventListener('input', function () { audio.currentTime = +range.value; lastT = audio.currentTime; draw(); });
    function onKey(e) { if (e.key === 'Escape' && !car.hidden) api.car(false); }
    document.addEventListener('keydown', onKey);

    if ('mediaSession' in navigator) {
      try {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: o.title || 'Sayback', artist: 'Sayback', album: o.album || '',
          artwork: [{ src: '_/theme/icon-512.png', sizes: '512x512', type: 'image/png' }]
        });
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
      play: function () { var p = audio.play(); if (p && p.catch) p.catch(function () {}); },
      pause: function () { audio.pause(); },
      toggle: function () { if (audio.paused) api.play(); else api.pause(); },
      seek: function (t) { audio.currentTime = Math.max(0, t); lastT = audio.currentTime; draw(); },
      skip: function (d) { api.seek((audio.currentTime || 0) + d); },
      speed: function (x) { rate = x; audio.playbackRate = x; speedBtn.textContent = (x === 1 ? '1' : String(x)) + '×'; },
      car: function (on) {
        car.hidden = !on;
        document.documentElement.classList.toggle('pl-car-open', !!on);
        if (on) car.querySelector('.pl-car-play').focus(); else playBtn.focus();
      },
      state: function () { return { playing: playing, position: audio.currentTime || 0, duration: audio.duration || dur, car: !car.hidden, rate: rate, src: audio.currentSrc || audio.src }; },
      destroy: function () {
        if (dead) return;
        if (playing) report(false);
        dead = true;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
        document.removeEventListener('keydown', onKey);
        document.documentElement.classList.remove('pl-car-open');
        if (car.parentNode) car.parentNode.removeChild(car);
        if ('mediaSession' in navigator) {
          ['play', 'pause', 'seekbackward', 'seekforward', 'nexttrack'].forEach(function (a) { try { navigator.mediaSession.setActionHandler(a, null); } catch (e) {} });
        }
        el.innerHTML = '';
      },
      _audio: audio
    };
    SB._player = api;  // tests drive the last player through this
    return api;
  };
})();
