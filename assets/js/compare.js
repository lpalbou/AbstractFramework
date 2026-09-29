/* ═══════════════════════════════════════════════════════════════════════════
   compare.js — before/after comparison with a draggable vertical divider.

   Markup (see deliver/fragments/compare.html):
     <figure class="cmp" data-compare style="--cmp-ratio: 1 / 1">
       <div class="cmp-stage">
         <div class="cmp-layer cmp-before"><img src="before.png" alt="..."></div>
         <div class="cmp-layer cmp-after"><img src="after.png" alt="..."></div>   (or a <video>)
         <span class="cmp-tag cmp-tag-before">Text-to-image</span>
         <span class="cmp-tag cmp-tag-after">Image edit</span>
       </div>
       <figcaption>...</figcaption>
     </figure>
   Options on the root: data-compare-start="50" (percent), data-compare-label
   (the slider's accessible name). The script adds the divider, a handle with
   role="slider" (arrow keys 1%, Shift+arrow 10%, Home/End, Page Up/Down) and,
   when a layer holds a video, a play/pause button. Video playback in view is
   managed by carousel3.js (give the video the `autoplay` attribute and
   data-c3-controls="0"). No animated intro: it opens at the start position
   under every motion setting and is always draggable.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var ICON_PAUSE = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  var ICON_PLAY = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';

  function Compare(root) {
    var self = this;
    this.root = root;
    this.stage = root.querySelector('.cmp-stage');
    if (!this.stage) return;
    var start = parseFloat(root.getAttribute('data-compare-start'));
    this.pos = isFinite(start) ? Math.min(100, Math.max(0, start)) : 50;

    this.divider = document.createElement('div');
    this.divider.className = 'cmp-divider';
    this.handle = document.createElement('div');
    this.handle.className = 'cmp-handle';
    this.handle.tabIndex = 0;
    this.handle.setAttribute('role', 'slider');
    this.handle.setAttribute('aria-orientation', 'horizontal');
    this.handle.setAttribute('aria-valuemin', '0');
    this.handle.setAttribute('aria-valuemax', '100');
    this.handle.setAttribute('aria-label', root.getAttribute('data-compare-label') || 'Comparison: drag to reveal the before or the after layer');
    this.handle.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 6 3 12 9 18"/><polyline points="15 6 21 12 15 18"/></svg>';
    this.divider.appendChild(this.handle);
    this.stage.appendChild(this.divider);

    this.set(this.pos);
    this.bind();

    var v = root.querySelector('video');
    if (v) this.videoToggle(v);
    root.classList.add('cmp-ready');
  }

  Compare.prototype.set = function (p) {
    this.pos = Math.min(100, Math.max(0, p));
    this.root.style.setProperty('--cmp-pos', this.pos + '%');
    this.handle.setAttribute('aria-valuenow', String(Math.round(this.pos)));
    this.handle.setAttribute('aria-valuetext', Math.round(this.pos) + '% before, ' + (100 - Math.round(this.pos)) + '% after');
  };

  Compare.prototype.fromEvent = function (e) {
    var r = this.stage.getBoundingClientRect();
    return ((e.clientX - r.left) / r.width) * 100;
  };

  Compare.prototype.bind = function () {
    var self = this;
    var dragging = false, id = null;
    this.stage.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      if (e.target.closest && e.target.closest('.cmp-video-toggle')) return;
      dragging = true; id = e.pointerId;
      try { self.stage.setPointerCapture(id); } catch (err) {}
      self.root.classList.add('is-dragging');
      self.set(self.fromEvent(e));
      self.handle.focus({ preventScroll: true });
      e.preventDefault();
    });
    this.stage.addEventListener('pointermove', function (e) {
      if (!dragging || e.pointerId !== id) return;
      self.set(self.fromEvent(e));
    });
    var end = function (e) {
      if (!dragging || (e && e.pointerId !== id)) return;
      dragging = false;
      self.root.classList.remove('is-dragging');
    };
    this.stage.addEventListener('pointerup', end);
    this.stage.addEventListener('pointercancel', end);
    this.handle.addEventListener('keydown', function (e) {
      var step = e.shiftKey ? 10 : 1, p = self.pos;
      switch (e.key) {
        case 'ArrowLeft': case 'ArrowDown': p -= step; break;
        case 'ArrowRight': case 'ArrowUp': p += step; break;
        case 'PageDown': p -= 10; break;
        case 'PageUp': p += 10; break;
        case 'Home': p = 0; break;
        case 'End': p = 100; break;
        default: return;
      }
      e.preventDefault();
      self.set(p);
    });
  };

  // A play/pause control for a video layer (WCAG 2.2.2). A pause made here counts
  // as the viewer's pause for carousel3.js's in-view autoplay.
  Compare.prototype.videoToggle = function (v) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cmp-video-toggle';
    var sync = function () {
      btn.innerHTML = v.paused ? ICON_PLAY : ICON_PAUSE;
      btn.setAttribute('aria-label', v.paused ? 'Play the video' : 'Pause the video');
    };
    btn.addEventListener('click', function () {
      if (v.paused) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
      else { v._afGestureAt = Date.now(); v.pause(); }
    });
    v.addEventListener('play', sync);
    v.addEventListener('pause', sync);
    sync();
    this.stage.appendChild(btn);
  };

  function init(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-compare]'), function (root) {
      if (root._cmp) return;
      root._cmp = new Compare(root);
    });
  }
  window.Compare = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();
})();
