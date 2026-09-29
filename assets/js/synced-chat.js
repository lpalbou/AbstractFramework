/* ═══════════════════════════════════════════════════════════════════════════
   synced-chat.js — one conversation, revealed at the same moment in every
   device frame (a shared timeline), with typing dots before each reply and a
   tool-approval gate that resolves in all frames when one frame approves.

   Markup (see deliver/fragments/synced-chat.html):
     <div class="sc" data-sc-root data-sc-from="laptop,phone,browser" data-sc-approvers="phone,browser,laptop">
       <div class="sc-grid" aria-hidden="true">
         <figure class="sc-frame" data-sc-frame="laptop" data-sc-name="MacBook Pro"> ... <div class="sc-feed">
             <div class="sc-u" data-sc="1">...</div>   user message (sent from data-sc-from[k])
             <div class="sc-a" data-sc="2">...</div>   assistant reply (typing dots first)
             <div class="sc-gate" data-sc="5">... <button class="sc-btn" data-sc-approve>...</button>
                  <span class="sc-resolved">...</span></div>   approval gate
             <div class="sc-u sc-auth" data-sc="6">Approved ...<small>from the <span class="sc-auth-from"></span></small></div>
                                                  the user's approval: the gate WAITS until this step
             <div class="sc-tool" data-sc="7">...</div>  tool result
         </div></figure> ...
       </div>
       <div class="sc-bar"><span class="sc-now"></span></div>
     </div>
   Every frame holds the same data-sc steps. Without JavaScript, or under
   prefers-reduced-motion, every message is visible and the gate is shown
   resolved; nothing moves.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var reduceMQ = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var ICON_PAUSE = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  var ICON_PLAY = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';

  function SyncedChat(root) {
    var self = this;
    this.root = root;
    this.frames = Array.prototype.slice.call(root.querySelectorAll('[data-sc-frame]'));
    this.feeds = this.frames.map(function (f) { return f.querySelector('.sc-feed'); });
    this.now = root.querySelector('.sc-now');
    this.bar = root.querySelector('.sc-bar');
    this.from = (root.getAttribute('data-sc-from') || '').split(',').map(function (s) { return s.trim(); });
    this.approvers = (root.getAttribute('data-sc-approvers') || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    this.staticText = this.now ? this.now.innerHTML : '';
    var seen = {};
    this.steps = [];
    root.querySelectorAll('.sc-feed > [data-sc]').forEach(function (n) {
      var k = parseInt(n.getAttribute('data-sc'), 10);
      if (!seen[k]) { seen[k] = true; self.steps.push(k); }
    });
    this.steps.sort(function (a, b) { return a - b; });
    this.loop = 0;
    this.timer = null;
    this.userPaused = false;
    this.visible = false;

    if (reduceMQ.matches) { this.showStatic(); }
    else { this.setup(); }
    if (reduceMQ.addEventListener) {
      reduceMQ.addEventListener('change', function () {
        if (reduceMQ.matches) { self.stop(); self.teardown(); self.showStatic(); }
        else { self.setup(); }
      });
    }
  }

  SyncedChat.prototype.frameName = function (key) {
    var f = this.frames.filter(function (x) { return x.getAttribute('data-sc-frame') === key; })[0];
    return f ? (f.getAttribute('data-sc-name') || key) : key;
  };

  SyncedChat.prototype.items = function (step) {
    return Array.prototype.slice.call(this.root.querySelectorAll('.sc-feed > [data-sc="' + step + '"]'));
  };

  SyncedChat.prototype.say = function (html) { if (this.now) this.now.innerHTML = html; };

  SyncedChat.prototype.showStatic = function () {
    var self = this;
    this.root.classList.remove('sc-anim', 'sc-fading');
    this.decorate();
    this.frames.forEach(function (f) { f.classList.remove('is-active', 'is-dim'); });
    // Static final state: every device labelled with its part in the story.
    this.from.forEach(function (key, i) {
      var f = self.frameEl(key), tag = f && f.querySelector('.sc-here');
      if (!tag) return;
      tag.textContent = (i + 1) + ' \u00b7 ' + (i === 0 ? 'started here' : 'continued here');
      f.classList.add('is-static-tag');
    });
    this.root.querySelectorAll('.sc-gate').forEach(function (g) { g.classList.add('is-resolved'); });
    this.root.querySelectorAll('.sc-typing').forEach(function (t) { t.remove(); });
    var who = this.approvers.length ? this.frameName(this.approvers[0]) : '';
    this.root.querySelectorAll('.sc-auth-from').forEach(function (n) { if (who) n.textContent = who; });
    if (this.toggle) this.toggle.hidden = true;
    this.say(this.staticText);
  };

  SyncedChat.prototype.teardown = function () {
    this.root.querySelectorAll('.is-in').forEach(function (n) { n.classList.remove('is-in'); });
    this.frames.forEach(function (f) { f.classList.remove('is-active', 'is-dim', 'is-static-tag'); });
    this.active = null;
  };

  // Labels above each frame and the travelling token (added once).
  SyncedChat.prototype.decorate = function () {
    if (this.decorated) return;
    this.decorated = true;
    this.grid = this.root.querySelector('.sc-grid');
    this.frames.forEach(function (f) {
      var tag = document.createElement('span');
      tag.className = 'sc-here';
      f.appendChild(tag);
    });
    if (this.grid) {
      this.token = document.createElement('span');
      this.token.className = 'sc-token';
      this.grid.appendChild(this.token);
    }
  };

  SyncedChat.prototype.setup = function () {
    var self = this;
    this.decorate();
    this.root.classList.add('sc-anim');
    if (!this.toggle && this.bar) {
      this.toggle = document.createElement('button');
      this.toggle.type = 'button';
      this.toggle.className = 'sc-toggle';
      this.toggle.addEventListener('click', function () {
        self.userPaused = !self.userPaused;
        self.syncToggle();
        if (self.userPaused) self.stop(); else self.play();
      });
      this.bar.appendChild(this.toggle);
    }
    if (this.toggle) this.toggle.hidden = false;
    this.syncToggle();
    this.reset();
    if (!this.io && 'IntersectionObserver' in window) {
      this.io = new IntersectionObserver(function (entries) {
        self.visible = entries[0].isIntersecting;
        if (self.visible) self.play(); else self.stop();
      }, { threshold: 0.25 });
      this.io.observe(this.root);
    } else if (!('IntersectionObserver' in window)) {
      this.visible = true; this.play();
    } else if (this.visible) { this.play(); }
  };

  SyncedChat.prototype.syncToggle = function () {
    if (!this.toggle) return;
    this.toggle.innerHTML = (this.userPaused ? ICON_PLAY + ' Play' : ICON_PAUSE + ' Pause') + ' animation';
    this.toggle.setAttribute('aria-pressed', this.userPaused ? 'true' : 'false');
  };

  SyncedChat.prototype.reset = function () {
    this.teardown();
    this.root.classList.remove('sc-fading');
    this.root.querySelectorAll('.sc-gate').forEach(function (g) { g.classList.remove('is-resolved'); });
    this.root.querySelectorAll('.sc-typing').forEach(function (t) { t.remove(); });
    this.root.querySelectorAll('.is-pressed').forEach(function (b) { b.classList.remove('is-pressed'); });
    // On a loop the conversation starts again from its first line, already shown.
    if (this.loop > 0 && this.steps.length) this.reveal(this.items(this.steps[0]));
    this.actions = this.build();
    this.pos = 0;
  };

  // The shared timeline for one loop: a list of {run, wait} actions. The gate
  // WAITS: nothing after it appears until one frame approves; the approval is
  // the user's own act, shown as a user line in every frame, then the run
  // continues.
  SyncedChat.prototype.build = function () {
    var self = this;
    var A = [];
    var userIdx = 0;
    var approver = this.approvers.length ? this.approvers[this.loop % this.approvers.length] : null;
    var gateItems = null;
    A.push({ run: function () { self.say('One conversation on the gateway, three clients following the same ledger live.'); }, wait: this.loop > 0 ? 400 : 900 });
    this.steps.forEach(function (step, k) {
      var items = self.items(step);
      if (!items.length) return;
      var first = items[0];
      if (first.classList.contains('sc-u') && !first.classList.contains('sc-auth')) {
        var src = self.from[userIdx % Math.max(self.from.length, 1)] || null;
        userIdx++;
        var already = k === 0 && self.loop > 0;
        var firstUser = userIdx === 1;
        A.push({ run: function () {
          self.highlight(src, firstUser ? 'starts here' : 'continues here');
          if (src) self.say((firstUser ? 'Started on the <b>' : 'Continued on the <b>') + self.frameName(src) + '</b>');
        }, wait: already ? 300 : 900 });
        A.push({ run: function () { self.reveal(items); }, wait: already ? 1000 : 1300 });
      } else if (first.classList.contains('sc-auth')) {
        // The user authorizes the pending tool call from one frame.
        A.push({ run: function () {
          var f = self.frameEl(approver);
          var btn = f && f.querySelector('[data-sc-approve]');
          if (btn) btn.classList.add('is-pressed');
          self.highlight(approver, 'approves here');
          if (approver) self.say('Approved on the <b>' + self.frameName(approver) + '</b>');
        }, wait: 900 });
        A.push({ run: function () {
          self.root.querySelectorAll('.is-pressed').forEach(function (b) { b.classList.remove('is-pressed'); });
          items.forEach(function (n) {
            var from = n.querySelector('.sc-auth-from');
            if (from && approver) from.textContent = self.frameName(approver);
          });
          self.reveal(items);
          if (gateItems) gateItems.forEach(function (g) { g.classList.add('is-resolved'); });
          self.say('Approved from the <b>' + self.frameName(approver) + '</b>: the wait resolves in all three, and the run continues');
        }, wait: 1800 });
      } else if (first.classList.contains('sc-a') || first.classList.contains('sc-gate')) {
        var gate = first.classList.contains('sc-gate');
        if (gate) gateItems = items;
        A.push({ run: function () { self.typing(true); }, wait: gate ? 900 : 1100 });
        A.push({ run: function () {
          self.typing(false); self.reveal(items);
          if (gate) self.say('The run <b>waits for your approval</b>, in every client. Nothing else happens until you answer.');
        }, wait: gate ? 3600 : Math.min(2600, 1000 + first.textContent.length * 14) });
      } else {
        A.push({ run: function () { self.reveal(items); }, wait: 1100 });
      }
    });
    A.push({ run: function () {}, wait: 4200 });
    A.push({ run: function () { self.root.classList.add('sc-fading'); }, wait: 700 });
    A.push({ run: function () { self.loop++; self.reset(); }, wait: 300 });
    return A;
  };

  SyncedChat.prototype.frameEl = function (key) {
    return this.frames.filter(function (x) { return x.getAttribute('data-sc-frame') === key; })[0] || null;
  };

  // The device that carries the conversation now: scaled up, ringed and labelled;
  // the other two dim; a token travels from the previous device to this one.
  SyncedChat.prototype.highlight = function (key, label) {
    var self = this;
    var prev = this.active || null;
    this.active = key || null;
    this.frames.forEach(function (f) {
      var on = !!key && f.getAttribute('data-sc-frame') === key;
      f.classList.toggle('is-active', on);
      f.classList.toggle('is-dim', !!key && !on);
      var tag = f.querySelector('.sc-here');
      if (tag && on && label) tag.textContent = label;
    });
    if (key && prev && prev !== key) this.travel(prev, key);
  };

  SyncedChat.prototype.center = function (key) {
    var f = this.frameEl(key), g = this.grid;
    if (!f || !g) return null;
    var dev = f.querySelector('.dv-laptop, .dv-phone, .dv-browser') || f;
    var r = dev.getBoundingClientRect(), gr = g.getBoundingClientRect();
    return { x: r.left - gr.left + r.width / 2, y: r.top - gr.top + r.height / 2 };
  };

  SyncedChat.prototype.travel = function (from, to) {
    var t = this.token, a = this.center(from), b = this.center(to);
    if (!t || !a || !b) return;
    t.style.transition = 'none';
    t.style.transform = 'translate(' + a.x + 'px,' + a.y + 'px)';
    t.classList.add('is-on');
    void t.offsetWidth;
    t.style.transition = '';
    t.style.transform = 'translate(' + b.x + 'px,' + b.y + 'px)';
    clearTimeout(this._tokTimer);
    this._tokTimer = setTimeout(function () { t.classList.remove('is-on'); }, 900);
  };

  SyncedChat.prototype.reveal = function (items) {
    items.forEach(function (n) { n.classList.add('is-in'); });
  };

  SyncedChat.prototype.typing = function (on) {
    this.feeds.forEach(function (feed) {
      var t = feed.querySelector('.sc-typing');
      if (on && !t) {
        t = document.createElement('div');
        t.className = 'sc-typing';
        t.innerHTML = '<i></i><i></i><i></i>';
        feed.appendChild(t);
      } else if (!on && t) { t.remove(); }
    });
  };

  SyncedChat.prototype.tick = function () {
    var self = this;
    this.timer = null;
    if (!this.actions || !this.actions.length) return;
    var a = this.actions[this.pos];
    this.pos++;
    a.run();
    if (this.pos >= this.actions.length) this.pos = 0; // reset() rebuilt the list on the last action
    this.timer = setTimeout(function () { self.tick(); }, a.wait);
  };

  SyncedChat.prototype.play = function () {
    if (this.timer || this.userPaused || reduceMQ.matches || !this.visible) return;
    this.tick();
  };
  SyncedChat.prototype.stop = function () { if (this.timer) { clearTimeout(this.timer); this.timer = null; } };

  function init(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-sc-root]'), function (root) {
      if (root._sc) return;
      root._sc = new SyncedChat(root);
    });
  }
  window.SyncedChat = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();
})();
