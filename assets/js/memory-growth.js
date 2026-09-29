/* ═══════════════════════════════════════════════════════════════════════════
   memory-growth.js — an entity's memory graph growing visit after visit, as an
   accelerated build-up (about 5 s), then a hold, then a loop.

   Markup (see deliver/fragments/memory-growth.html):
     <figure class="mg" data-mg
             data-mg-src="assets/data/entity-graph/visit-1.json,assets/data/entity-graph/visit-2.json,...">
       <div class="mg-canvas"></div>
       <figcaption class="mg-caption">...</figcaption>
     </figure>
   Each JSON file is a snapshot after one visit: { nodes: [...], edges: [...] }
   (also accepted: { graph: { nodes, edges } }). Node fields read: id |
   record_id | graph_id, kind | type, label | title, created_at | observed_at |
   timestamp | ts | seq. Edge fields read: source | from | src | subject,
   target | to | dst | object, relation | predicate | kind. Snapshots are merged
   in order; a node belongs to the first visit that contains it and appears in
   creation order. The identity core (value, purpose, trait) is pinned at the
   centre. Without data-mg-src the component draws a PLACEHOLDER graph of the
   same shape and says so on screen.
   Reduced motion: the final graph, no autoplay; the scrubber still works.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var SVGNS = 'http://www.w3.org/2000/svg';
  var reduceMQ = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var BUILD_MS = 5000, HOLD_MS = 2600, FADE_MS = 500;

  // AbstractMemory record kinds (records.py MEMORY_RECORD_KINDS); identity kinds first.
  var KIND_COLORS = {
    value: '#818cf8', purpose: '#a78bfa', trait: '#c4b5fd',
    interest: '#e879f9', episode: '#34d399', memory: '#2dd4bf', lesson: '#fbbf24',
    diary: '#f472b6', question: '#38bdf8', answer: '#7dd3fc', summary: '#f59e0b',
    dream: '#fb7185', world_model: '#22d3ee', realization: '#f0abfc', claim: '#fcd34d',
    decision: '#a3e635', plan: '#bef264', instruction: '#94a3b8'
  };
  var CORE = { value: 1, purpose: 1, trait: 1 };

  function S(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function H(tag, cls, parent, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  function hash(str) { var h = 2166136261; for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967296; }
  function pick(o, keys) { for (var i = 0; i < keys.length; i++) if (o[keys[i]] !== undefined && o[keys[i]] !== null) return o[keys[i]]; return undefined; }

  // ── data ────────────────────────────────────────────────────────────────
  function merge(snapshots) {
    var nodes = [], byId = {}, edges = [], seenE = {};
    snapshots.forEach(function (snap, vi) {
      var g = snap && snap.graph ? snap.graph : snap || {};
      (g.nodes || []).forEach(function (n, ni) {
        var id = String(pick(n, ['id', 'record_id', 'graph_id']));
        if (byId[id]) return;
        var t = pick(n, ['created_at', 'observed_at', 'timestamp', 'ts', 'seq']);
        var node = { id: id, kind: String(pick(n, ['kind', 'type']) || 'memory'), label: String(pick(n, ['label', 'title']) || ''),
                     visit: vi + 1, t: t === undefined ? null : t, ord: ni };
        byId[id] = node; nodes.push(node);
      });
      (g.edges || []).forEach(function (e) {
        var a = String(pick(e, ['source', 'from', 'src', 'subject'])), b = String(pick(e, ['target', 'to', 'dst', 'object']));
        var rel = String(pick(e, ['relation', 'predicate', 'kind']) || '');
        var key = a + '|' + b + '|' + rel;
        if (seenE[key]) return;
        seenE[key] = true;
        edges.push({ a: a, b: b, rel: rel, visit: vi + 1 });
      });
    });
    nodes.sort(function (x, y) {
      if (!!CORE[x.kind] !== !!CORE[y.kind]) return CORE[x.kind] ? -1 : 1;
      if (x.visit !== y.visit) return x.visit - y.visit;
      if (x.t !== null && y.t !== null && x.t !== y.t) return x.t < y.t ? -1 : 1;
      return x.ord - y.ord;
    });
    edges = edges.filter(function (e) { return byId[e.a] && byId[e.b]; });
    return { nodes: nodes, byId: byId, edges: edges, visits: snapshots.length };
  }

  // Placeholder of the same shape as W2's per-visit snapshots (clearly labelled on screen).
  function placeholder() {
    var snaps = [], nodes = [], edges = [], n = 0;
    function add(kind, label) { var id = 'p' + (n++); nodes.push({ id: id, kind: kind, label: label, seq: n }); return id; }
    function link(a, b, rel) { edges.push({ source: a, target: b, relation: rel }); }
    var core = [add('value', 'intellectual_honesty'), add('value', 'shared_vulnerability'), add('value', 'care_in_action'),
                add('purpose', 'help the humans you work with'), add('trait', 'ask before assuming')];
    var eps = [], interest = null, question = null;
    for (var v = 1; v <= 4; v++) {
      var ep = add('episode', 'visit ' + v);
      if (eps.length) link(ep, eps[eps.length - 1], 'continues');
      eps.push(ep);
      var mems = [];
      for (var m = 0; m < 4 + (v % 2) * 2; m++) { var r = add('memory', 'visit ' + v + ' turn ' + (m + 1)); link(r, ep, 'from_session'); if (mems.length) link(r, mems[mems.length - 1], 'mentions'); mems.push(r); }
      if (v === 1) { interest = add('interest', 'restore tooling'); link(interest, mems[1], 'derived_from'); }
      if (v >= 2) { var ls = add('lesson', 'lesson ' + (v - 1)); link(ls, ep, 'derived_from'); link(ls, mems[0], 'supports'); }
      if (v === 2) { question = add('question', 'why did it fail?'); link(question, ep, 'written_amid'); var d = add('diary', 'diary entry'); link(d, ep, 'written_amid'); }
      if (v === 3) { var an = add('answer', 'answer'); link(an, question, 'answers'); var su = add('summary', 'summary'); link(su, eps[0], 'summarizes'); link(su, eps[1], 'summarizes'); var in2 = add('interest', 'backup schedules'); link(in2, mems[2], 'derived_from'); }
      if (v === 4) { var wm = add('world_model', 'the home lab'); link(wm, mems[0], 'derived_from'); link(wm, eps[2], 'derived_from'); var d2 = add('diary', 'diary entry'); link(d2, ep, 'written_amid'); link(mems[3], interest, 'mentions'); }
      snaps.push({ nodes: nodes.slice(), edges: edges.slice() });
    }
    return snaps;
  }

  // ── layout: deterministic, identity core pinned at the centre; each visit
  // grows in its own sector around it (clockwise from the top), refined by a
  // small force pass in unit-disc coordinates, then stretched to the canvas.
  function layout(g, W, Hh) {
    var V = Math.max(1, g.visits), sector = Math.PI * 2 / V;
    var core = g.nodes.filter(function (n) { return CORE[n.kind]; });
    core.forEach(function (n, i) {
      var a = -Math.PI / 2 + (i / Math.max(core.length, 1)) * Math.PI * 2;
      n.u = Math.cos(a) * 0.12; n.v = Math.sin(a) * 0.12; n.pin = true;
    });
    var rest = g.nodes.filter(function (n) { return !CORE[n.kind]; });
    rest.forEach(function (n) {
      n.home = -Math.PI / 2 + (n.visit - 0.5) * sector;
      var a = n.home + (hash(n.id) - 0.5) * sector * 0.8, r = 0.38 + hash(n.id + 'r') * 0.52;
      n.u = Math.cos(a) * r; n.v = Math.sin(a) * r;
    });
    var all = g.nodes, k = 0.11;
    for (var it = 0; it < 260; it++) {
      var temp = 0.06 * (1 - it / 260) + 0.004;
      all.forEach(function (p) { p.fu = 0; p.fv = 0; });
      for (var i = 0; i < all.length; i++) {
        var p = all[i];
        for (var j = i + 1; j < all.length; j++) {
          var q = all[j], du = p.u - q.u, dv = p.v - q.v, d2 = du * du + dv * dv + 1e-4;
          if (d2 > 0.25) continue;
          var f = (k * k) / d2 * 0.12;
          p.fu += du * f; p.fv += dv * f; q.fu -= du * f; q.fv -= dv * f;
        }
      }
      g.edges.forEach(function (e) {
        var a = g.byId[e.a], b = g.byId[e.b];
        if (a.visit !== b.visit && !CORE[a.kind] && !CORE[b.kind]) return; // cross-visit links do not pull sectors together
        var du = b.u - a.u, dv = b.v - a.v, d = Math.sqrt(du * du + dv * dv) + 1e-4, f = (d - k) * 0.35;
        a.fu += du / d * f; a.fv += dv / d * f; b.fu -= du / d * f; b.fv -= dv / d * f;
      });
      rest.forEach(function (p) {
        // stay in the visit's sector and in the ring between the core and the rim
        var r = Math.sqrt(p.u * p.u + p.v * p.v) + 1e-4, a = Math.atan2(p.v, p.u);
        var da = Math.atan2(Math.sin(p.home - a), Math.cos(p.home - a));
        var lim = sector * 0.42;
        if (Math.abs(da) > lim) { var push = (Math.abs(da) - lim) * Math.sign(da) * 0.5; p.fu += -Math.sin(a) * push * r; p.fv += Math.cos(a) * push * r; }
        if (r < 0.32) { p.fu += p.u / r * (0.32 - r); p.fv += p.v / r * (0.32 - r); }
        if (r > 0.94) { p.fu -= p.u / r * (r - 0.94); p.fv -= p.v / r * (r - 0.94); }
      });
      rest.forEach(function (p) {
        var m = Math.sqrt(p.fu * p.fu + p.fv * p.fv) + 1e-6, step = Math.min(m, temp);
        p.u += p.fu / m * step; p.v += p.fv / m * step;
      });
    }
    var sx = W / 2 - 36, sy = Hh / 2 - 36;
    all.forEach(function (n) { n.x = W / 2 + n.u * sx; n.y = Hh / 2 + n.v * sy; });
  }

  // ── component ───────────────────────────────────────────────────────────
  function MemoryGrowth(root) {
    var self = this;
    this.root = root;
    this.canvas = root.querySelector('.mg-canvas') || H('div', 'mg-canvas', root);
    this.progress = reduceMQ.matches ? 1 : 0;
    this.playing = false;
    this.userPaused = reduceMQ.matches;
    var src = (root.getAttribute('data-mg-src') || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    this.isPlaceholder = !src.length;
    var ready = function (snaps) {
      self.g = merge(snaps);
      self.build();
      self.observe();
    };
    if (src.length) {
      Promise.all(src.map(function (u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ': HTTP ' + r.status); return r.json(); }); }))
        .then(ready)
        .catch(function (err) {
          // Fail loudly: show the error instead of silently drawing something else.
          self.canvas.innerHTML = '<p class="mg-error">Memory graph data failed to load: ' + String(err.message || err).replace(/</g, '&lt;') + '</p>';
        });
    } else {
      ready(placeholder());
    }
  }

  MemoryGrowth.prototype.build = function () {
    var self = this, g = this.g;
    this.canvas.innerHTML = '';
    if (this.isPlaceholder) H('span', 'mg-badge', this.canvas, 'Placeholder data');
    this.svgWrap = H('div', 'mg-svg', this.canvas);
    this.visitTag = H('div', 'mg-visit', this.canvas);
    var ctr = H('div', 'mg-controls', this.root.querySelector('.mg-canvas'));
    this.playBtn = H('button', 'mg-play', ctr);
    this.playBtn.type = 'button';
    this.playBtn.addEventListener('click', function () {
      if (self.playing) { self.userPaused = true; self.pause(); }
      else { self.userPaused = false; if (self.progress >= 1) self.progress = 0; self.play(true); }
    });
    this.range = H('input', 'mg-range', ctr);
    this.range.type = 'range'; this.range.min = '0'; this.range.max = '1000'; this.range.step = '1';
    this.range.setAttribute('aria-label', 'Build-up of the memory graph');
    this.range.addEventListener('input', function () { self.userPaused = true; self.pause(); self.progress = +self.range.value / 1000; self.paint(); });

    // legend with the kinds present, identity first
    var kinds = [];
    g.nodes.forEach(function (n) { if (kinds.indexOf(n.kind) < 0) kinds.push(n.kind); });
    var leg = H('div', 'mg-legend', this.canvas);
    kinds.forEach(function (k) {
      H('span', null, leg, '<i style="background:' + (KIND_COLORS[k] || '#9898b0') + '"></i>' + k + (CORE[k] ? ' <small>(identity)</small>' : ''));
    });

    this.layoutFor();
    if ('ResizeObserver' in window) {
      new ResizeObserver(function () { var n = self.narrowNow(); if (n !== self.narrow) self.layoutFor(); }).observe(this.canvas);
    }
    if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function () { if (reduceMQ.matches) { self.pause(); self.progress = 1; self.paint(); } });
    this.syncBtn();
  };

  MemoryGrowth.prototype.narrowNow = function () { return (this.canvas.clientWidth || 800) < 560; };

  MemoryGrowth.prototype.layoutFor = function () {
    var g = this.g, self = this;
    this.narrow = this.narrowNow();
    var W = 1000, Hh = this.narrow ? 1000 : 600;
    layout(g, W, Hh);
    var svg = S('svg', { viewBox: '0 0 ' + W + ' ' + Hh, role: 'img', 'aria-label': 'An entity’s memory graph growing over ' + g.visits + ' visits: ' + g.nodes.length + ' records and ' + g.edges.length + ' relations' });
    var gE = S('g', { class: 'mg-edges' }, svg), gN = S('g', { class: 'mg-nodes' }, svg);
    var n = g.nodes.length;
    // creation order drives the timeline; the core is present from the start
    var coreCount = g.nodes.filter(function (x) { return CORE[x.kind]; }).length;
    g.nodes.forEach(function (node, i) {
      node.at = CORE[node.kind] ? 0 : 0.04 + 0.92 * (i - coreCount) / Math.max(1, n - coreCount);
      var core = !!CORE[node.kind], col = KIND_COLORS[node.kind] || '#9898b0';
      var r = core ? (self.narrow ? 16 : 13) : (self.narrow ? 11 : 8.5);
      var grp = S('g', { class: 'mg-node' + (core ? ' is-core' : '') }, gN);
      S('circle', { cx: node.x, cy: node.y, r: r, fill: col, 'fill-opacity': core ? 0.9 : 0.75, stroke: col, 'stroke-opacity': 0.9 }, grp);
      var t = S('title', null, grp); t.textContent = node.kind + (node.label ? ': ' + node.label : '') + ' (visit ' + node.visit + ')';
      node.el = grp;
    });
    g.edges.forEach(function (e) {
      var a = g.byId[e.a], b = g.byId[e.b];
      e.at = Math.max(a.at, b.at) + 0.01;
      var len = Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
      var line = S('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: 'mg-edge rel-' + e.rel.replace(/[^a-z_]/gi, ''), 'stroke-dasharray': len }, gE);
      line.style.strokeDashoffset = String(len);
      var t = S('title', null, line); t.textContent = e.rel;
      e.el = line; e.len = len;
    });
    // identity core labels
    var coreNodes = g.nodes.filter(function (x) { return CORE[x.kind]; });
    var gc = S('g', { class: 'mg-core-label' }, svg);
    var ct = S('text', { x: W / 2, y: Hh / 2 + 0.12 * (Hh / 2 - 36) + (this.narrow ? 62 : 40), 'text-anchor': 'middle', style: this.narrow ? 'font-size:30px' : '' }, gc);
    ct.textContent = 'identity core';
    this.svgWrap.innerHTML = '';
    this.svgWrap.appendChild(svg);
    this.paint(true);
  };

  MemoryGrowth.prototype.paint = function () {
    var p = this.progress, g = this.g, visit = 1;
    g.nodes.forEach(function (n) { var on = p >= n.at; if (n.el.classList.contains('is-on') !== on) n.el.classList.toggle('is-on', on); if (on && !CORE[n.kind]) visit = Math.max(visit, n.visit); });
    g.edges.forEach(function (e) { var on = p >= e.at; if (e.el.classList.contains('is-on') !== on) { e.el.classList.toggle('is-on', on); e.el.style.strokeDashoffset = on ? '0' : String(e.len); } });
    this.range.value = String(Math.round(p * 1000));
    var shown = g.nodes.filter(function (n) { return p >= n.at; }).length;
    this.range.setAttribute('aria-valuetext', 'visit ' + visit + ' of ' + g.visits + ', ' + shown + ' records');
    this.visitTag.innerHTML = 'visit <b>' + visit + '</b> of ' + g.visits + ' &middot; ' + shown + ' records';
  };

  MemoryGrowth.prototype.syncBtn = function () {
    this.playBtn.innerHTML = this.playing
      ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>'
      : '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
    this.playBtn.setAttribute('aria-label', this.playing ? 'Pause the build-up' : 'Play the build-up');
  };

  MemoryGrowth.prototype.play = function (fromUser) {
    var self = this;
    if (this.playing || (this.userPaused && !fromUser) || (reduceMQ.matches && !fromUser) || (!this.visible && !fromUser)) return;
    this.playing = true; this.syncBtn();
    var last = null, holdUntil = null;
    var frame = function (ts) {
      if (!self.playing) return;
      if (last === null) last = ts;
      var dt = ts - last; last = ts;
      if (self.progress < 1) {
        self.progress = Math.min(1, self.progress + dt / BUILD_MS);
        self.paint();
      } else {
        if (holdUntil === null) holdUntil = ts + HOLD_MS;
        if (ts >= holdUntil) {
          self.root.classList.add('mg-fading');
          setTimeout(function () {
            self.root.classList.remove('mg-fading');
            self.progress = 0; self.paint(); holdUntil = null; last = null;
            if (self.playing) self.raf = requestAnimationFrame(frame);
          }, FADE_MS);
          return;
        }
      }
      self.raf = requestAnimationFrame(frame);
    };
    this.raf = requestAnimationFrame(frame);
  };
  MemoryGrowth.prototype.pause = function () { this.playing = false; if (this.raf) cancelAnimationFrame(this.raf); this.syncBtn(); };

  MemoryGrowth.prototype.observe = function () {
    var self = this;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        self.visible = entries[0].isIntersecting;
        if (self.visible) self.play(); else if (self.playing) self.pause();
      }, { threshold: 0.3 }).observe(this.root);
    } else { this.visible = true; this.play(); }
  };

  function init(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-mg]'), function (root) {
      if (root._mg) return;
      root._mg = new MemoryGrowth(root);
    });
  }
  window.MemoryGrowth = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();
})();
