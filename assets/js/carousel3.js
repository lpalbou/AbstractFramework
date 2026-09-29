/* ═══════════════════════════════════════════════════════════════════════════
   carousel3.js — three-panel perspective carousel (previous | current | next)

   Markup (see deliver/fragments/carousel.html):
     <div class="c3" data-c3 aria-label="Generated images">
       <div class="c3-stage">
         <figure class="c3-slide"> <img ...> <figcaption>...</figcaption> </figure>
         <figure class="c3-slide"> <video controls ...></video> <figcaption>...</figcaption> </figure>
       </div>
     </div>
   The script adds the arrows, the dots and the live caption. Options on the
   root: data-c3-autoplay="7000" (ms; adds a pause button; never runs under
   prefers-reduced-motion), data-c3-start="0".
   Vanilla JS, no dependencies. Safe to load with `defer`.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var reduceMQ = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };

  function el(tag, cls, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }

  // ── video autoplay while in view (Q10) ────────────────────────────────
  // A managed video (the `autoplay` attribute, plus muted/loop/playsinline)
  // plays muted while it is on screen or focused, and pauses otherwise. The
  // script takes over from the native attribute so that it can pause off
  // screen and honour prefers-reduced-motion (no autoplay; controls shown).
  // A viewer's own pause is respected until the video leaves and comes back.
  function manage(v) {
    if (v._afManaged) return;
    v._afManaged = true;
    v.removeAttribute('autoplay');
    v.autoplay = false;
    v.muted = true;
    v.setAttribute('playsinline', '');
    if (!v.hasAttribute('controls') && v.dataset.c3Controls === undefined) v.setAttribute('controls', '');
    v.addEventListener('pause', function () {
      if (v._afAuto) { v._afAuto = false; return; }
      if (!v.ended) v._afUserPaused = true;
    });
    v.addEventListener('play', function () { v._afUserPaused = false; });
    if (!v.paused) autoPause(v);
  }
  function autoPlay(v) {
    if (reduceMQ.matches || v._afUserPaused || !v.paused) return;
    v.muted = true;
    var pr = v.play();
    if (pr && pr.catch) pr.catch(function () {});
  }
  function autoPause(v, forget) {
    if (forget) v._afUserPaused = false;
    if (v.paused) return;
    v._afAuto = true;
    v.pause();
  }
  function hasFocus(el) { return el.contains(document.activeElement); }

  var ICON_PREV = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>';
  var ICON_NEXT = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>';
  var ICON_PAUSE = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  var ICON_PLAY = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';

  function Carousel(root) {
    this.root = root;
    this.stage = root.querySelector('.c3-stage');
    this.slides = Array.prototype.slice.call(root.querySelectorAll('.c3-slide'));
    this.n = this.slides.length;
    this.index = Math.min(Math.max(parseInt(root.getAttribute('data-c3-start') || '0', 10) || 0, 0), Math.max(this.n - 1, 0));
    this.timer = null;
    this.userPaused = false;
    if (!this.stage || this.n === 0) return;
    this.build();
    this.update(false);
    this.bind();
    root.classList.add('c3-ready');
  }

  Carousel.prototype.label = function () {
    return this.root.getAttribute('aria-label') || 'Carousel';
  };

  Carousel.prototype.captionOf = function (i) {
    var fc = this.slides[i].querySelector('figcaption, .c3-slide-caption');
    return fc ? fc.textContent.replace(/\s+/g, ' ').trim() : '';
  };

  Carousel.prototype.build = function () {
    var self = this;
    var root = this.root;
    root.setAttribute('role', 'region');
    root.setAttribute('aria-roledescription', 'carousel');
    if (!root.hasAttribute('aria-label')) root.setAttribute('aria-label', 'Carousel');

    this.slides.forEach(function (s, i) {
      s.setAttribute('role', 'group');
      s.setAttribute('aria-roledescription', 'slide');
      s.setAttribute('aria-label', (i + 1) + ' of ' + self.n);
      s.dataset.c3Index = String(i);
      var v = s.querySelector('video');
      if (v) { s.classList.add('c3-has-video'); v.dataset.c3Controls = v.hasAttribute('controls') || v.hasAttribute('autoplay') ? '1' : '0'; if (v.hasAttribute('autoplay')) manage(v); }
    });

    var kind = root.querySelector('video') && !root.querySelector('img:not([aria-hidden="true"])') ? 'video' : 'image';
    if (this.n > 1) {
      this.prevBtn = el('button', 'c3-arrow c3-prev', { type: 'button', 'aria-label': 'Previous ' + kind });
      this.prevBtn.innerHTML = ICON_PREV;
      this.nextBtn = el('button', 'c3-arrow c3-next', { type: 'button', 'aria-label': 'Next ' + kind });
      this.nextBtn.innerHTML = ICON_NEXT;
      this.stage.appendChild(this.prevBtn);
      this.stage.appendChild(this.nextBtn);
    }

    var bar = el('div', 'c3-bar');
    this.dotsWrap = el('div', 'c3-dots', { role: 'group', 'aria-label': 'Choose a slide' });
    this.dots = this.slides.map(function (s, i) {
      var d = el('button', 'c3-dot', { type: 'button', 'aria-label': 'Show ' + kind + ' ' + (i + 1) + ' of ' + self.n });
      d.addEventListener('click', function () { self.go(i, true); });
      self.dotsWrap.appendChild(d);
      return d;
    });
    if (this.n > 1) bar.appendChild(this.dotsWrap);

    var ap = parseInt(root.getAttribute('data-c3-autoplay') || '0', 10);
    this.autoplayMs = ap > 0 && this.n > 1 ? Math.max(ap, 3000) : 0;
    if (this.autoplayMs) {
      this.playBtn = el('button', 'c3-play', { type: 'button' });
      this.playBtn.addEventListener('click', function () {
        self.userPaused = !self.userPaused;
        self.syncPlayBtn();
        if (self.userPaused) self.stop(); else self.start();
      });
      bar.appendChild(this.playBtn);
    }
    root.appendChild(bar);

    this.live = el('p', 'c3-live', { 'aria-live': 'off', 'aria-atomic': 'true' });
    root.appendChild(this.live);
  };

  Carousel.prototype.syncPlayBtn = function () {
    if (!this.playBtn) return;
    var paused = this.userPaused || reduceMQ.matches;
    this.playBtn.innerHTML = paused ? ICON_PLAY : ICON_PAUSE;
    this.playBtn.setAttribute('aria-label', paused ? 'Start automatic slide show' : 'Pause automatic slide show');
  };

  // Position of slide i relative to the current one, wrapped to [-n/2, n/2].
  Carousel.prototype.offset = function (i) {
    var d = i - this.index;
    var n = this.n;
    if (n <= 2) return d;
    if (d > n / 2) d -= n;
    if (d < -n / 2) d += n;
    return d;
  };

  Carousel.prototype.update = function (announce) {
    var self = this;
    this.slides.forEach(function (s, i) {
      var off = self.offset(i);
      s.classList.remove('is-center', 'is-prev', 'is-next', 'is-far-prev', 'is-far-next');
      var pos = off === 0 ? 'is-center' : off === -1 ? 'is-prev' : off === 1 ? 'is-next' : off < 0 ? 'is-far-prev' : 'is-far-next';
      // With two slides the other one sits on the right only; mirror it on the left
      // visually is confusing, so keep it as "next".
      s.classList.add(pos);
      var center = off === 0;
      s.setAttribute('aria-hidden', center ? 'false' : 'true');
      Array.prototype.forEach.call(s.querySelectorAll('a, button, video, audio, input, [tabindex]'), function (f) {
        if (center) {
          if (f.dataset.c3Tab !== undefined) { if (f.dataset.c3Tab === '') f.removeAttribute('tabindex'); else f.setAttribute('tabindex', f.dataset.c3Tab); delete f.dataset.c3Tab; }
        } else if (f.dataset.c3Tab === undefined) {
          f.dataset.c3Tab = f.getAttribute('tabindex') || '';
          f.setAttribute('tabindex', '-1');
        }
      });
      var v = s.querySelector('video');
      if (v) {
        if (center) {
          if (v.dataset.c3Controls === '1') v.setAttribute('controls', '');
        } else {
          if (v._afManaged) autoPause(v, true); else if (!v.paused) v.pause();
          v.removeAttribute('controls');
        }
      }
    });
    this.dots.forEach(function (d, i) {
      if (i === self.index) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current');
    });
    var cap = this.captionOf(this.index);
    // Visible caption of the centre slide; announced only after a user action
    // (never during autoplay, per the WAI-ARIA carousel pattern).
    this.live.setAttribute('aria-live', announce ? 'polite' : 'off');
    this.live.innerHTML = '';
    var count = el('span', 'c3-count');
    count.textContent = (this.index + 1) + ' of ' + this.n;
    var capEl = el('span', 'c3-cap');
    capEl.textContent = cap;
    this.live.appendChild(count);
    this.live.appendChild(capEl);
    this.syncVideos();

  };

  Carousel.prototype.syncVideos = function () {
    var self = this;
    var active = !!this.inView || hasFocus(this.root);
    this.slides.forEach(function (s, i) {
      var v = s.querySelector('video');
      if (!v || !v._afManaged) return;
      if (i === self.index && active) autoPlay(v);
      else autoPause(v, i !== self.index || !self.inView);
    });
  };

  Carousel.prototype.go = function (i, fromUser) {
    if (this.n < 2) return;
    this.index = ((i % this.n) + this.n) % this.n;
    this.update(!!fromUser);
    if (fromUser) this.restart();
  };
  Carousel.prototype.next = function (u) { this.go(this.index + 1, u); };
  Carousel.prototype.prev = function (u) { this.go(this.index - 1, u); };

  Carousel.prototype.start = function () {
    var self = this;
    this.stop();
    if (!this.autoplayMs || this.userPaused || reduceMQ.matches || this.hovered || this.focused || !this.visible) return;
    this.timer = setInterval(function () {
      var cur = self.slides[self.index].querySelector('video');
      if (cur && !cur.paused) return; // never advance away from a playing video
      self.go(self.index + 1, false);
    }, this.autoplayMs);
  };
  Carousel.prototype.stop = function () { if (this.timer) { clearInterval(this.timer); this.timer = null; } };
  Carousel.prototype.restart = function () { if (this.autoplayMs) this.start(); };

  Carousel.prototype.bind = function () {
    var self = this;
    var root = this.root;
    if (this.prevBtn) this.prevBtn.addEventListener('click', function () { self.prev(true); });
    if (this.nextBtn) this.nextBtn.addEventListener('click', function () { self.next(true); });

    // Clicking a side panel brings it to the centre.
    this.slides.forEach(function (s, i) {
      s.addEventListener('click', function (e) {
        if (s.classList.contains('is-center')) return;
        e.preventDefault();
        self.go(i, true);
      });
    });

    // Arrow keys anywhere inside the carousel, except inside a focused media element or field.
    root.addEventListener('keydown', function (e) {
      var t = e.target;
      if (t && (t.tagName === 'VIDEO' || t.tagName === 'AUDIO' || t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); self.prev(true); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); self.next(true); }
      else if (e.key === 'Home') { e.preventDefault(); self.go(0, true); }
      else if (e.key === 'End') { e.preventDefault(); self.go(self.n - 1, true); }
    });

    // Swipe (touch and pen; mouse drags are left to video scrubbing and text selection).
    var sx = null, sy = null, sid = null;
    this.stage.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse') return;
      sx = e.clientX; sy = e.clientY; sid = e.pointerId;
    }, { passive: true });
    this.stage.addEventListener('pointerup', function (e) {
      if (sx === null || e.pointerId !== sid) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      sx = sy = sid = null;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.2) { if (dx < 0) self.next(true); else self.prev(true); }
    }, { passive: true });
    this.stage.addEventListener('pointercancel', function () { sx = sy = sid = null; }, { passive: true });

    // Autoplay pauses on hover and focus, and only runs while visible.
    if (this.autoplayMs) {
      root.addEventListener('mouseenter', function () { self.hovered = true; self.stop(); });
      root.addEventListener('mouseleave', function () { self.hovered = false; self.start(); });
      root.addEventListener('focusin', function () { self.focused = true; self.stop(); });
      root.addEventListener('focusout', function (e) { if (!root.contains(e.relatedTarget)) { self.focused = false; self.start(); } });
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          self.visible = entries[0].isIntersecting;
          if (self.visible) self.start(); else self.stop();
        }, { threshold: 0.3 }).observe(root);
      } else { this.visible = true; this.start(); }
      var onRM = function () { self.syncPlayBtn(); if (reduceMQ.matches) self.stop(); else self.start(); };
      if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', onRM);
      this.syncPlayBtn();
    }

    // Managed videos: play the centre one while the carousel is on screen or focused.
    if (this.root.querySelector('video')) {
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          self.inView = entries[0].isIntersecting;
          self.syncVideos();
        }, { threshold: 0.4 }).observe(root);
      } else { this.inView = true; }
      root.addEventListener('focusin', function () { self.syncVideos(); });
      root.addEventListener('focusout', function () { setTimeout(function () { self.syncVideos(); }, 0); });
      if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function () {
        if (reduceMQ.matches) self.slides.forEach(function (s) { var v = s.querySelector('video'); if (v && v._afManaged) autoPause(v); });
        else self.syncVideos();
      });
    }

    // A video that starts playing in the centre stops the slide show from moving on.
    this.slides.forEach(function (s) {
      var v = s.querySelector('video');
      if (v) v.addEventListener('play', function () { if (!s.classList.contains('is-center')) v.pause(); });
    });
  };

  // Standalone videos with the `autoplay` attribute (outside a carousel).
  function initStandalone(scope) {
    var vids = Array.prototype.filter.call((scope || document).querySelectorAll('video[autoplay]'), function (v) {
      return !v.closest('[data-c3]') && !v._afManaged;
    });
    if (!vids.length) return;
    var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        e.target._afInView = e.isIntersecting;
        if (e.isIntersecting || hasFocus(e.target)) autoPlay(e.target); else autoPause(e.target, true);
      });
    }, { threshold: 0.4 }) : null;
    vids.forEach(function (v) {
      manage(v);
      v.addEventListener('focus', function () { autoPlay(v); });
      v.addEventListener('blur', function () { if (!v._afInView) autoPause(v); });
      if (io) io.observe(v); else autoPlay(v);
    });
    if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function () {
      vids.forEach(function (v) { if (reduceMQ.matches) autoPause(v); else if (v._afInView) autoPlay(v); });
    });
  }

  function init(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-c3]'), function (root) {
      if (root._c3) return;
      root._c3 = new Carousel(root);
    });
    initStandalone(scope);
  }

  window.Carousel3 = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();
})();
