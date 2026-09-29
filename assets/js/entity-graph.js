/* ═══════════════════════════════════════════════════════════════════════════
   entity-graph.js — an illustrated timeline of two entities' memory graphs.

   Vocabulary follows AbstractMemory, AbstractRuntime and AbstractGateway (see
   deliver/fragments/COMPONENTS.md for the source lines): the spark (values,
   traits, purposes) is fixed for life and present in every session; every
   session is formed into memory (episodes, successes and failures alike);
   lessons and the diary are what the entity chooses to keep; facts are
   triples with valid_from / valid_until that close or are superseded, never
   deleted; recall in a later session strengthens only what was used; sleep
   is deterministic and only proposes (a summary with `summarizes` edges, at
   most one dream with `mentions` links; sources unchanged); the four phases
   are visit / work / personal / sleep (AbstractRuntime identity/spec/entity_phases.vendored.json:49-84, identity/life.py:232-235; entities have no role field).

   Markup (see deliver/fragments/entity-graph.html):
     <div class="eg" data-eg aria-label="..."></div>
   The script renders the panels, the scrubber and the log. Everything is
   drawn with inline SVG sized to the container, so labels stay legible from
   390 px to 1440 px. Under prefers-reduced-motion the graph opens on its
   final state and never plays by itself; the scrubber still works.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var SVGNS = 'http://www.w3.org/2000/svg';
  var reduceMQ = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };

  var LANES = [
    { key: 'identity', label: 'identity', sub: ['spark:', 'values,', 'traits'] },
    { key: 'role', label: 'phase', sub: ['visit ·', 'work ·', 'personal ·', 'sleep'] },
    { key: 'purpose', label: 'purpose', sub: ['spark:', 'purposes'] },
    { key: 'history', label: 'history', sub: ['formed', 'per session'] },
    { key: 'experience', label: 'experience', sub: ['lessons,', 'facts,', 'diary,', 'sleep', 'proposals'] }
  ];
  var PHASES = ['visit', 'work', 'personal', 'sleep'];
  var COLORS = {
    identity: '#818cf8', purpose: '#a78bfa', ok: '#34d399', failed: '#f472b6', experience: '#fbbf24'
  };
  var SEQ_MAX = 32;

  var DATA = [
    {
      key: 'castor', name: 'Castor', note: 'long-lived', born: 0,
      phases: [[0, 'personal'], [2, 'visit'], [5, 'work'], [12, 'sleep'], [15, 'work'], [18, 'personal'], [20, 'work'], [22, 'visit'], [25, 'sleep'], [28, 'personal']],
      nodes: [
        { id: 'v1', lane: 'identity', kind: 'value', label: 'honesty', title: 'value (spark): intellectual_honesty', born: 0 },
        { id: 'v2', lane: 'identity', kind: 'value', label: 'care', title: 'value (spark): care_in_action', born: 0 },
        { id: 't1', lane: 'identity', kind: 'trait', label: 'ask first', title: 'trait (spark): ask before assuming', born: 0 },
        { id: 'p1', lane: 'purpose', kind: 'purpose', label: 'help people', title: 'purpose (spark): help the humans you work with', born: 0 },
        { id: 'r3', lane: 'history', kind: 'episode', status: 'ok', label: 'visit 3', title: 'episode formed from visit 3: backup strategy, went well', born: 3 },
        { id: 'r7', lane: 'history', kind: 'episode', status: 'failed', label: 'work 7', title: 'episode formed from work session 7: restore test, failed', born: 7 },
        { id: 'r9', lane: 'history', kind: 'episode', status: 'ok', label: 'work 9', title: 'episode formed from work session 9: restore test, passed', born: 9 },
        { id: 'r16', lane: 'history', kind: 'episode', status: 'ok', label: 'work 16', title: 'episode formed from work session 16: hourly backups, done', born: 16 },
        { id: 'r23', lane: 'history', kind: 'episode', status: 'ok', label: 'visit 23', title: 'episode formed from visit 23: review, went well', born: 23 },
        { id: 'l1', lane: 'experience', kind: 'lesson', label: 'verify restore', title: 'lesson: verify a restore before sign-off', born: 10 },
        { id: 'c1', lane: 'experience', kind: 'fact', label: 'nightly', title: 'fact (triple): home-lab, backup_schedule, nightly', born: 11, until: 20, window: true },
        { id: 's1', lane: 'experience', kind: 'summary', label: 'summary', title: 'summary proposed by consolidation: restore test (inactive until reviewed)', born: 13, proposal: true },
        { id: 'y1', lane: 'experience', kind: 'diary', label: 'diary', title: 'diary entry (the book keeps the words; the graph keeps the act of writing)', born: 18 },
        { id: 'c2', lane: 'experience', kind: 'fact', label: 'hourly', title: 'fact (triple): home-lab, backup_schedule, hourly', born: 20, window: true },
        { id: 'd1', lane: 'experience', kind: 'dream', label: 'dream', title: 'dream proposed during sleep (review-gated, never a fact)', born: 26, proposal: true }
      ],
      edges: [
        { type: 'summarizes', from: 's1', to: 'r7', at: 13 }, { type: 'summarizes', from: 's1', to: 'r9', at: 13 },
        { type: 'supersedes', from: 'c2', to: 'c1', at: 20 },
        { type: 'mentions', from: 'd1', to: 'r16', at: 26 }, { type: 'mentions', from: 'd1', to: 'r23', at: 26 }
      ],
      recalls: [
        { at: 9, from: 'r9', to: ['r7'] },
        { at: 16, from: 'r16', to: ['l1', 'c1'] },
        { at: 23, from: 'r23', to: ['l1', 'c2'] }
      ],
      log: {
        0: 'Castor is created from its spark: values, traits and purposes, fixed for life and present in every conversation.',
        2: 'Visit: a person talks with Castor.',
        3: 'Formation: the visit is formed into memory as an episode.',
        5: 'Work: Castor is summoned into a work session.',
        7: 'The restore test fails. The failure is formed into memory like any success.',
        9: 'Recall: the new session recalls the failed attempt from memory. The restore test passes.',
        10: 'At the end of the session Castor writes down a lesson it chooses to keep.',
        11: 'A fact forms: (home-lab, backup_schedule, nightly), valid from seq 11.',
        12: 'Sleep.',
        13: 'Consolidation during sleep proposes a summary of the two restore sessions (inactive until reviewed); the sources stay unchanged.',
        15: 'Work.',
        16: 'Recall: the lesson and the nightly fact light up; recall strengthens what the session used.',
        18: 'Personal time: Castor writes a diary entry. The diary is hash-chained and never deleted.',
        20: 'The nightly fact closes (valid until seq 20); the hourly fact supersedes it. Nothing is deleted.',
        22: 'Visit.',
        23: 'Recall: the lesson and the hourly fact, in a later conversation.',
        25: 'Sleep.',
        26: 'Sleep proposes one dream, weakly linked to recent sessions; a proposal, never a fact.',
        28: 'Personal time. History: 5 sessions formed into memory, 4 went well, 1 failed.'
      }
    },
    {
      key: 'ephemeral', name: 'Ephemeral', note: 'created later', born: 6,
      phases: [[6, 'personal'], [7, 'work'], [12, 'sleep'], [14, 'work'], [19, 'personal'], [21, 'work'], [25, 'sleep'], [28, 'work']],
      nodes: [
        { id: 'v1', lane: 'identity', kind: 'value', label: 'honesty', title: 'value (spark): intellectual_honesty', born: 6 },
        { id: 't1', lane: 'identity', kind: 'trait', label: 'verify first', title: 'trait (spark): verify before asserting', born: 6 },
        { id: 'p1', lane: 'purpose', kind: 'purpose', label: 'triage mail', title: 'purpose (spark): help triage the inbox', born: 6 },
        { id: 'r8', lane: 'history', kind: 'episode', status: 'ok', label: 'work 8', title: 'episode formed from work session 8: inbox triage, done', born: 8 },
        { id: 'r14', lane: 'history', kind: 'episode', status: 'failed', label: 'work 14', title: 'episode formed from work session 14: mail API call refused, failed', born: 14 },
        { id: 'r17', lane: 'history', kind: 'episode', status: 'failed', label: 'work 17', title: 'episode formed from work session 17: mail API call refused, failed', born: 17 },
        { id: 'r21', lane: 'history', kind: 'episode', status: 'ok', label: 'work 21', title: 'episode formed from work session 21: inbox triage, done', born: 21 },
        { id: 'r29', lane: 'history', kind: 'episode', status: 'ok', label: 'work 29', title: 'episode formed from work session 29: draft replies, done', born: 29 },
        { id: 'c1', lane: 'experience', kind: 'fact', label: 'read-only', title: 'fact (triple): mail_api, token_scope, read-only', born: 15, until: 24, window: true },
        { id: 'l1', lane: 'experience', kind: 'lesson', label: 'check scope', title: 'lesson: check the token scope before calling', born: 18 },
        { id: 'y1', lane: 'experience', kind: 'diary', label: 'diary', title: 'diary entry (a question: why is the scope read-only?)', born: 20 },
        { id: 'c2', lane: 'experience', kind: 'fact', label: 'read-write', title: 'fact (triple): mail_api, token_scope, read-write', born: 24, window: true },
        { id: 's1', lane: 'experience', kind: 'summary', label: 'summary', title: 'summary proposed by consolidation: mail API call refused (inactive until reviewed)', born: 26, proposal: true }
      ],
      edges: [
        { type: 'supersedes', from: 'c2', to: 'c1', at: 24 },
        { type: 'summarizes', from: 's1', to: 'r14', at: 26 }, { type: 'summarizes', from: 's1', to: 'r17', at: 26 }
      ],
      recalls: [
        { at: 17, from: 'r17', to: ['r14', 'c1'] },
        { at: 21, from: 'r21', to: ['l1', 'y1'] },
        { at: 29, from: 'r29', to: ['l1', 'c2'] }
      ],
      log: {
        0: 'Not created yet.',
        6: 'Ephemeral is created from its own spark: values, traits and purposes, fixed for life.',
        7: 'Work.',
        8: 'Formation: the work session is formed into memory as an episode.',
        12: 'Sleep. Nothing to consolidate: a quiet night is a valid night.',
        14: 'The mail API refuses the call. The failure is formed into memory, with a feeling about tool:mail_api.',
        15: 'A fact forms: (mail_api, token_scope, read-only), valid from seq 15.',
        17: 'Same error. Recall: the earlier failure and the read-only fact light up.',
        18: 'At the end of the session Ephemeral writes down a lesson it chooses to keep.',
        19: 'Personal time.',
        20: 'Ephemeral writes a question in its diary: why is the scope read-only?',
        21: 'Recall: the lesson and the diary question; it asks for a wider scope and the session succeeds.',
        24: 'The read-only fact closes (valid until seq 24); read-write supersedes it.',
        25: 'Sleep.',
        26: 'Consolidation during sleep proposes a summary of the two refused sessions (inactive until reviewed).',
        28: 'Work.',
        29: 'Recall: the lesson and the new fact. History: 5 sessions formed into memory, 3 went well, 2 failed.'
      }
    }
  ];

  function S(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
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
  function stripTags(s) { return String(s).replace(/<[^>]+>/g, ''); }

  function phaseAt(ent, seq) {
    var p = null;
    ent.phases.forEach(function (x) { if (x[0] <= seq) p = x[1]; });
    return p;
  }
  function logAt(ent, seq) {
    var best = null, at = -1;
    Object.keys(ent.log).forEach(function (k) { var n = +k; if (n <= seq && n > at) { at = n; best = ent.log[k]; } });
    return best === null ? '' : '<span class="eg-sr">seq ' + at + ': </span>' + best;
  }
  function wrapLabel(text, maxChars) {
    var words = [], lines = [], cur = '';
    text.split(' ').forEach(function (w) {
      if (w.length > maxChars && w.indexOf('-') > 0) { var i = w.indexOf('-'); words.push(w.slice(0, i + 1)); words.push(w.slice(i + 1)); }
      else words.push(w);
    });
    words.forEach(function (w) {
      if (!cur) cur = w;
      else if ((cur + ' ' + w).length <= maxChars && cur.slice(-1) !== '-') cur += ' ' + w;
      else if (cur.slice(-1) === '-' && (cur + w).length <= maxChars) cur += w;
      else { lines.push(cur); cur = w; }
    });
    if (cur) lines.push(cur);
    if (lines.length > 2) lines = [lines[0], lines.slice(1).join(' ')];
    return lines;
  }

  function EntityGraph(root) {
    var self = this;
    this.root = root;
    this.data = DATA;
    this.seq = reduceMQ.matches ? SEQ_MAX : 0;
    this.playing = false;
    this.userPaused = reduceMQ.matches;
    this.visible = false;
    this.timer = null;
    this.prevSeq = null;
    this.build();
    this.render();
    if ('ResizeObserver' in window) {
      var lastW = 0;
      new ResizeObserver(function () {
        var w = self.panels[0].canvas.clientWidth;
        if (Math.abs(w - lastW) > 2) { lastW = w; self.prevSeq = self.seq; self.render(); }
      }).observe(root);
    } else {
      window.addEventListener('resize', function () { self.prevSeq = self.seq; self.render(); });
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        self.visible = entries[0].isIntersecting;
        if (self.visible) self.play(); else self.pause(false);
      }, { threshold: 0.3 }).observe(root);
    }
    if (reduceMQ.addEventListener) {
      reduceMQ.addEventListener('change', function () {
        if (reduceMQ.matches) { self.pause(true); self.setSeq(SEQ_MAX, false); }
      });
    }
  }

  EntityGraph.prototype.build = function () {
    var self = this;
    var root = this.root;
    root.setAttribute('role', 'group');
    if (!root.hasAttribute('aria-label')) root.setAttribute('aria-label', 'Illustration: two entities and their memory graphs over time');
    root.innerHTML = '';
    var wrap = H('div', 'eg-panels', root);
    this.panels = this.data.map(function (ent) {
      var fig = H('figure', 'eg-panel', wrap);
      var head = H('div', 'eg-head', fig);
      H('div', 'eg-name', head, ent.name + '<small>' + ent.note + '</small>');
      var phase = H('div', 'eg-phase', head);
      var canvas = H('div', 'eg-canvas', fig);
      var now = H('p', 'eg-now', fig);
      now.setAttribute('aria-live', 'off');
      return { ent: ent, fig: fig, phase: phase, canvas: canvas, now: now };
    });

    var ctr = H('div', 'eg-controls', root);
    this.playBtn = H('button', 'eg-play', ctr);
    this.playBtn.type = 'button';
    this.playBtn.addEventListener('click', function () {
      if (self.playing) self.pause(true);
      else { self.userPaused = false; if (self.seq >= SEQ_MAX) self.setSeq(0, false); self.play(true); }
    });
    var id = 'eg-range-' + Math.random().toString(36).slice(2, 8);
    var lab = H('label', 'eg-sr', ctr, 'Journal sequence');
    lab.setAttribute('for', id);
    this.range = H('input', 'eg-range', ctr);
    this.range.type = 'range'; this.range.min = '0'; this.range.max = String(SEQ_MAX); this.range.step = '1'; this.range.id = id;
    this.range.addEventListener('input', function () { self.pause(true); self.setSeq(+self.range.value, true); });
    this.seqOut = H('output', 'eg-seq', ctr);
    this.seqOut.setAttribute('for', id);

    H('div', 'eg-legend', root,
      '<span><i style="background:' + COLORS.identity + '"></i>identity</span>' +
      '<span><i style="background:' + COLORS.purpose + '"></i>purpose</span>' +
      '<span><i style="background:' + COLORS.ok + '"></i>session went well</span>' +
      '<span><i style="background:' + COLORS.failed + '"></i>session failed</span>' +
      '<span><i style="background:' + COLORS.experience + '"></i>lesson, fact, diary</span>' +
      '<span><i style="background:transparent;border:1.5px dotted ' + COLORS.experience + '"></i>sleep proposal (summary, dream)</span>' +
      '<span><i class="l-line" style="border-color:#22d3ee"></i>recall</span>' +
      '<span><i class="l-dash" style="border-color:rgba(251,191,36,.8)"></i>summarizes</span>' +
      '<span><i class="l-dash" style="border-color:rgba(152,152,176,.8)"></i>supersedes</span>' +
      '<span><i style="background:transparent;border:1.5px dashed #9898b0"></i>closed (valid until)</span>');
    this.syncBtn();
  };

  EntityGraph.prototype.syncBtn = function () {
    this.playBtn.innerHTML = this.playing
      ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>'
      : '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
    this.playBtn.setAttribute('aria-label', this.playing ? 'Pause the timeline' : 'Play the timeline');
  };

  EntityGraph.prototype.setSeq = function (seq, announce) {
    this.prevSeq = this.seq;
    this.seq = Math.max(0, Math.min(SEQ_MAX, seq));
    this.render(announce);
  };

  EntityGraph.prototype.play = function (fromUser) {
    var self = this;
    if (this.playing || this.userPaused || reduceMQ.matches && !fromUser) return;
    if (!this.visible && !fromUser) return;
    this.playing = true;
    this.syncBtn();
    var step = function () {
      if (!self.playing) return;
      if (self.seq >= SEQ_MAX) {
        self.timer = setTimeout(function () { if (!self.playing) return; self.setSeq(0, false); self.timer = setTimeout(step, 900); }, 3800);
        return;
      }
      self.setSeq(self.seq + 1, false);
      self.timer = setTimeout(step, 780);
    };
    this.timer = setTimeout(step, 500);
  };

  EntityGraph.prototype.pause = function (byUser) {
    if (byUser) this.userPaused = true;
    this.playing = false;
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    this.syncBtn();
  };

  EntityGraph.prototype.render = function (announce) {
    var self = this;
    this.range.value = String(this.seq);
    this.seqOut.textContent = 'seq ' + this.seq + ' / ' + SEQ_MAX;
    this.range.setAttribute('aria-valuetext', 'journal sequence ' + this.seq + ' of ' + SEQ_MAX);
    this.panels.forEach(function (p) {
      var ph = p.ent.born <= self.seq ? phaseAt(p.ent, self.seq) : null;
      p.phase.innerHTML = ph ? 'phase <b>' + ph + '</b>' : 'not created';
      p.now.setAttribute('aria-live', announce ? 'polite' : 'off');
      p.now.innerHTML = logAt(p.ent, self.seq);
      self.draw(p);
    });
  };

  EntityGraph.prototype.draw = function (p) {
    var ent = p.ent, seq = this.seq, prev = this.prevSeq;
    var W = Math.max(280, p.canvas.clientWidth || 520);
    var narrow = W < 440;
    var gutter = narrow ? 60 : 96;
    var slots = 1;
    this.data.forEach(function (e) { var c = {}; e.nodes.forEach(function (n) { c[n.lane] = (c[n.lane] || 0) + 1; slots = Math.max(slots, c[n.lane]); }); });
    var avail = W - gutter - 4;
    var slotW = avail / slots;
    var laneH = { identity: 74, role: 70, purpose: 70, history: 74, experience: 78 };
    var laneY = {}, y = 6;
    LANES.forEach(function (l) { laneY[l.key] = y; y += laneH[l.key]; });
    var H_ = y + 4;

    var svg = S('svg', { viewBox: '0 0 ' + W + ' ' + H_, width: W, height: H_, role: 'img', 'aria-label': ent.name + ': memory graph at journal sequence ' + seq });
    var desc = S('desc', null, svg);
    desc.textContent = stripTags(logAt(ent, seq));

    // lanes
    var gL = S('g', null, svg);
    LANES.forEach(function (l, i) {
      var ly = laneY[l.key];
      if (i > 0) S('line', { class: 'eg-lane-line', x1: 0, x2: W, y1: ly, y2: ly }, gL);
      var t = S('text', { class: 'eg-lane-label', x: 0, y: ly + 16 }, gL);
      t.textContent = l.label;
      l.sub.forEach(function (s, j) {
        var st = S('text', { class: 'eg-lane-sub', x: 0, y: ly + 28 + j * (narrow ? 10 : 11), style: narrow ? 'font-size:8.5px' : '' }, gL);
        st.textContent = s;
      });
    });

    if (seq < ent.born) {
      var u = S('text', { class: 'eg-unborn', x: gutter + avail / 2, y: H_ / 2, 'text-anchor': 'middle' }, svg);
      u.textContent = 'created at seq ' + ent.born + ' (engram)';
      p.canvas.innerHTML = '';
      p.canvas.appendChild(svg);
      return;
    }

    // role lane: the four phases, the current one lit
    var ph = phaseAt(ent, seq);
    var pillW = Math.min(84, (avail - 12) / 4), pillH = 22;
    var ry = laneY.role + (laneH.role - pillH) / 2;
    PHASES.forEach(function (name, i) {
      var g = S('g', { class: 'eg-phase-pill' + (name === ph ? ' is-on' : '') }, svg);
      var px = gutter + i * (pillW + 4);
      S('rect', { x: px, y: ry, width: pillW, height: pillH, rx: 11 }, g);
      var t = S('text', { x: px + pillW / 2, y: ry + 15, 'text-anchor': 'middle' }, g);
      t.textContent = name;
    });

    // node positions (slot by order of formation inside each lane)
    var pos = {}, laneCount = {};
    ent.nodes.forEach(function (n) {
      var k = laneCount[n.lane] || 0;
      laneCount[n.lane] = k + 1;
      pos[n.id] = { x: gutter + (k + 0.5) * slotW, y: laneY[n.lane] + 18 };
    });

    // recall counts up to seq (commit_selection strengthens what was used)
    var counts = {};
    ent.recalls.forEach(function (r) { if (r.at <= seq) r.to.forEach(function (id) { counts[id] = (counts[id] || 0) + 1; }); });
    var activeRecall = ent.recalls.filter(function (r) { return r.at <= seq && seq < r.at + 2; })[0] || null;
    var runNow = ent.nodes.some(function (n) { return n.lane === 'history' && n.born <= seq && seq < n.born + 2; });

    // edges
    var gE = S('g', null, svg);
    function curve(a, b) {
      if (Math.abs(a.y - b.y) < 2) {
        var lift = Math.min(30, Math.abs(a.x - b.x) / 2 + 8);
        return 'M' + a.x + ' ' + (a.y - 8) + ' Q' + ((a.x + b.x) / 2) + ' ' + (a.y - 8 - lift) + ' ' + b.x + ' ' + (b.y - 8);
      }
      var my = (a.y + b.y) / 2;
      return 'M' + a.x + ' ' + a.y + ' C' + a.x + ' ' + my + ' ' + b.x + ' ' + my + ' ' + b.x + ' ' + b.y;
    }
    ent.edges.forEach(function (e) {
      if (e.at > seq) return;
      var fresh = prev !== null && prev < e.at && e.at <= seq;
      S('path', { class: 'eg-edge ' + e.type + (fresh ? ' is-new' : ''), d: curve(pos[e.from], pos[e.to]) }, gE);
    });
    if (activeRecall) {
      activeRecall.to.forEach(function (id) {
        S('path', { class: 'eg-edge recall', d: curve(pos[activeRecall.from], pos[id]) }, gE);
      });
    }

    // nodes
    var maxChars = Math.max(5, Math.floor((slotW - 2) / (narrow ? 5.1 : 5.6)));
    var gN = S('g', null, svg);
    ent.nodes.forEach(function (n) {
      if (n.born > seq) return;
      var c = pos[n.id];
      var closed = n.until !== undefined && seq >= n.until;
      var fresh = prev !== null && prev < n.born && n.born <= seq;
      var color = n.lane === 'history' ? COLORS[n.status] : COLORS[n.lane] || COLORS.experience;
      var cls = 'eg-node' + (closed ? ' is-closed' : '') + (fresh ? ' is-new' : '');
      if (!closed && runNow && (n.lane === 'identity' || n.lane === 'purpose')) cls += ' is-self';
      if (activeRecall && activeRecall.to.indexOf(n.id) >= 0) cls += ' is-recalled';
      var g = S('g', { class: cls }, gN);
      var r = (narrow ? 7 : 8.5) + Math.min(counts[n.id] || 0, 3) * 1.7;
      if (n.proposal) {
        S('circle', { cx: c.x, cy: c.y, r: r, fill: color, 'fill-opacity': .12, stroke: color, 'stroke-dasharray': '2 2' }, g);
      } else {
        S('circle', { cx: c.x, cy: c.y, r: r, fill: color, 'fill-opacity': .28, stroke: color }, g);
      }
      if (n.lane === 'history') {
        var mark = S('text', { x: c.x, y: c.y + 3.5, 'text-anchor': 'middle', style: 'font-size:9px;font-weight:700;fill:' + color }, g);
        mark.textContent = n.status === 'ok' ? '✓' : '✕';
      }
      var lines = wrapLabel(n.label, maxChars);
      lines.forEach(function (ln, i) {
        var t = S('text', { class: 'eg-node-label', x: c.x, y: c.y + r + 12 + i * 11, 'text-anchor': 'middle', style: narrow ? 'font-size:9.2px' : '' }, g);
        t.textContent = ln;
      });
      var win = null;
      if (n.window || n.until !== undefined) {
        win = closed ? n.born + '→' + n.until : 'since ' + n.born;
        var wt = S('text', { class: 'eg-node-win', x: c.x, y: c.y + r + 12 + lines.length * 11, 'text-anchor': 'middle' }, g);
        wt.textContent = win;
      }
      var title = S('title', null, g);
      title.textContent = n.title + ' · formed at seq ' + n.born +
        (n.until !== undefined ? (closed ? ' · closed at seq ' + n.until : ' · valid until seq ' + n.until) : '') +
        (counts[n.id] ? ' · recalled ' + counts[n.id] + 'x' : '');
    });

    p.canvas.innerHTML = '';
    p.canvas.appendChild(svg);
  };

  function init(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-eg]'), function (root) {
      if (root._eg) return;
      root._eg = new EntityGraph(root);
    });
  }
  window.EntityGraph = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();
})();
