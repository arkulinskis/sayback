/* Spoken Miles offline lessons: saves lesson MP3s (and what the lesson page needs to show them) in this browser's
   Cache Storage, so they play with no signal: tunnels, the countryside, a car park. Wrapped by Pages/Downloads and
   used by Pages/Lesson (a saved lesson plays from the phone even when online: no data used).
     SB.offline.start(items, {onProgress(done, total, mb), onDone(saved, failed)})   items = [{course, code, url, meta, mb}]
     SB.offline.cancel()            SB.offline.busy()
     SB.offline.saved()             -> Promise [{course, code, mb}]
     SB.offline.has(course, code)   -> Promise bool
     SB.offline.url(course, code)   -> Promise blob: URL or ''   (for the <audio>)
     SB.offline.meta(course, code)  -> Promise lesson dict or null
     SB.offline.remove(course, codes) -> Promise number removed
     SB.offline.space()             -> Promise {used, quota} in MB (0 when the browser won't say)
     SB.offline.persist()           -> Promise bool (asks the browser not to clear saved lessons when space runs low)
     SB.offline.files(urls)         downloads MP3 files one after another (the links carry "attachment")
     SB.install.can() / SB.install.prompt() / SB.install.ios() / SB.install.standalone()
   The lesson files live in a private Cloudflare R2 bucket: saving needs the bucket's CORS rule to allow GET from the
   app's address (README: "Before selling"). Nothing here runs unless the member presses a Save button. */
(function () {
  var SB = window.SB = window.SB || {};
  var CACHE = 'sm-lessons-v1';
  var BASE = '/__sm_offline__/';
  var job = null;

  function key(course, code, ext) { return location.origin + BASE + course + '/' + code + (ext || '.mp3'); }
  function ok() { return typeof caches !== 'undefined' && !!window.fetch; }
  function open() { return caches.open(CACHE); }

  function saveOne(cache, it, signal) {
    return fetch(it.url, { mode: 'cors', credentials: 'omit', signal: signal }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return cache.put(key(it.course, it.code), new Response(r.body, { headers: { 'Content-Type': 'audio/mpeg' } }));
    }).then(function () {
      var meta = Object.assign({}, it.meta || {}, { saved_at: Date.now(), mb: it.mb || 0 });
      return cache.put(key(it.course, it.code, '.json'),
        new Response(JSON.stringify(meta), { headers: { 'Content-Type': 'application/json' } }));
    });
  }

  SB.offline = {
    supported: function () { return ok(); },
    busy: function () { return !!job; },
    start: function (items, o) {
      o = o || {};
      if (!ok() || job) { if (o.onDone) o.onDone(0, items.length); return; }
      var ctl = window.AbortController ? new AbortController() : null;
      job = { ctl: ctl, stop: false };
      var me = job, done = 0, failed = 0, mb = 0;
      open().then(function (cache) {
        var i = 0;
        function next() {
          if (me.stop || i >= items.length) {
            job = null;
            if (o.onDone) o.onDone(done, failed + (items.length - i));
            return;
          }
          var it = items[i++];
          saveOne(cache, it, ctl && ctl.signal).then(function () { done++; mb += it.mb || 0; })
            .catch(function () { failed++; })
            .then(function () { if (o.onProgress) o.onProgress(done + failed, items.length, Math.round(mb)); next(); });
        }
        next();
      }).catch(function () { job = null; if (o.onDone) o.onDone(0, items.length); });
    },
    cancel: function () { if (job) { job.stop = true; if (job.ctl) job.ctl.abort(); } },
    saved: function () {
      if (!ok()) return Promise.resolve([]);
      return open().then(function (cache) {
        return cache.keys().then(function (reqs) {
          var metas = reqs.filter(function (r) { return /\.json$/.test(r.url); });
          return Promise.all(metas.map(function (r) {
            return cache.match(r).then(function (res) { return res ? res.json() : null; }).catch(function () { return null; });
          }));
        });
      }).then(function (list) {
        return list.filter(Boolean).map(function (m) {
          return { course: m.course, code: m.code, mb: m.mb || 0, title_en: (m.title || {}).en || m.code, title_es: (m.title || {}).es || '', level: m.level, n: m.n };
        });
      }).catch(function () { return []; });
    },
    has: function (course, code) {
      if (!ok()) return Promise.resolve(false);
      return open().then(function (c) { return c.match(key(course, code)); }).then(function (r) { return !!r; })
        .catch(function () { return false; });
    },
    url: function (course, code) {
      if (!ok()) return Promise.resolve('');
      return open().then(function (c) { return c.match(key(course, code)); }).then(function (r) {
        return r ? r.blob().then(function (b) { return URL.createObjectURL(b); }) : '';
      }).catch(function () { return ''; });
    },
    meta: function (course, code) {
      if (!ok()) return Promise.resolve(null);
      return open().then(function (c) { return c.match(key(course, code, '.json')); })
        .then(function (r) { return r ? r.json() : null; }).catch(function () { return null; });
    },
    remove: function (course, codes) {
      if (!ok()) return Promise.resolve(0);
      return open().then(function (c) {
        return Promise.all((codes || []).map(function (code) {
          return Promise.all([c.delete(key(course, code)), c.delete(key(course, code, '.json'))])
            .then(function (r) { return r[0] ? 1 : 0; });
        }));
      }).then(function (n) { return n.reduce(function (a, b) { return a + b; }, 0); }).catch(function () { return 0; });
    },
    space: function () {
      if (!navigator.storage || !navigator.storage.estimate) return Promise.resolve({ used: 0, quota: 0 });
      return navigator.storage.estimate().then(function (e) {
        return { used: Math.round((e.usage || 0) / 1e6), quota: Math.round((e.quota || 0) / 1e6) };
      }).catch(function () { return { used: 0, quota: 0 }; });
    },
    persist: function () {
      if (!navigator.storage || !navigator.storage.persist) return Promise.resolve(false);
      return navigator.storage.persist().catch(function () { return false; });
    },
    files: function (urls) {
      (urls || []).forEach(function (u, i) {
        setTimeout(function () {
          var a = document.createElement('a');
          a.href = u; a.rel = 'noopener'; a.download = '';
          document.body.appendChild(a); a.click(); a.remove();
        }, i * 1400);
      });
    }
  };

  // Add to home screen: Chrome/Edge/Android fire beforeinstallprompt; iPhone uses Share > Add to Home Screen.
  var deferred = null;
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); deferred = e; });
  window.addEventListener('appinstalled', function () { deferred = null; });
  SB.install = {
    can: function () { return !!deferred; },
    prompt: function () {
      if (!deferred) return Promise.resolve(false);
      var d = deferred; deferred = null; d.prompt();
      return d.userChoice.then(function (c) { return c && c.outcome === 'accepted'; }).catch(function () { return false; });
    },
    ios: function () { return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream; },
    standalone: function () {
      return (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
    }
  };
})();
