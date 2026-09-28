document.addEventListener('DOMContentLoaded', () => {

  /* ── Nav scroll effect ── */
  const nav = document.querySelector('.nav');
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 50);
    lastScroll = y;
  }, { passive: true });

  /* ── Smooth scroll for anchor links ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const href = a.getAttribute('href');
      if (href === '#') { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
      const el = document.querySelector(href);
      if (el) {
        e.preventDefault();
        history.replaceState(null, '', href);
        const offset = 80;
        const y = el.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    });
  });

  /* ── Scroll reveal with stagger ── */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        const delay = entry.target.dataset.delay || 0;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, parseInt(delay));
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal').forEach((el, i) => {
    if (!el.dataset.delay && el.parentElement) {
      const siblings = el.parentElement.querySelectorAll(':scope > .reveal');
      const idx = Array.from(siblings).indexOf(el);
      if (idx > 0) el.dataset.delay = idx * 80;
    }
    revealObserver.observe(el);
  });

  /* ── Animated counter for stats ── */
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = el.dataset.count;
        if (!target) return;
        const isPercent = target.includes('%');
        const num = parseInt(target);
        const suffix = target.replace(/[\d]/g, '');
        let current = 0;
        const step = Math.max(1, Math.floor(num / 40));
        const timer = setInterval(() => {
          current += step;
          if (current >= num) {
            current = num;
            clearInterval(timer);
          }
          el.textContent = current + suffix;
        }, 30);
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-num[data-count]').forEach(el => {
    counterObserver.observe(el);
  });

  /* ── Copy code buttons ── */
  document.querySelectorAll('.code-block, .hero-code').forEach(block => {
    if (block.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.setAttribute('aria-label', 'Copy code');
    btn.addEventListener('click', () => {
      const code = block.querySelector('code') || block.querySelector('pre') || block;
      const text = block.dataset.copy || code.textContent.trim();
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      });
    });
    block.style.position = 'relative';
    block.appendChild(btn);
  });

  /* ── Mobile menu toggle ── */
  const toggle = document.querySelector('.mobile-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    links.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => links.classList.remove('open'));
    });
  }

  /* ── Image lightbox ── */
  document.querySelectorAll('.showcase-img img, .gallery-item img, .get-card .shot img, .figure img, .j-body img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      const overlay = document.createElement('div');
      overlay.className = 'lightbox-overlay';
      const big = document.createElement('img');
      big.src = img.currentSrc || img.src;
      big.alt = img.alt || '';
      overlay.setAttribute('role', 'dialog');
      overlay.setAttribute('aria-label', img.alt || 'Image');
      overlay.appendChild(big);
      overlay.addEventListener('click', () => overlay.remove());
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', esc); }
      });
      document.body.appendChild(overlay);
    });
  });

  /* ── Tab system (ARIA tabs, arrow keys) ── */
  document.querySelectorAll('.code-tabs').forEach(tabs => {
    const nav = tabs.querySelector('.tab-nav');
    const buttons = Array.from(tabs.querySelectorAll('.tab-btn'));
    const panels = tabs.querySelectorAll('.tab-panel');
    if (nav) nav.setAttribute('role', 'tablist');
    function activate(btn, focus) {
      const target = btn.dataset.tab;
      buttons.forEach(b => {
        const on = b === btn;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.tabIndex = on ? 0 : -1;
      });
      panels.forEach(p => p.classList.toggle('active', p.id === 'tab-' + target));
      if (focus) btn.focus();
    }
    buttons.forEach((btn, i) => {
      btn.setAttribute('role', 'tab');
      btn.setAttribute('aria-controls', 'tab-' + btn.dataset.tab);
      btn.id = btn.id || ('tabbtn-' + btn.dataset.tab);
      const panel = tabs.querySelector('#tab-' + btn.dataset.tab);
      if (panel) { panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', btn.id); }
      btn.setAttribute('aria-selected', btn.classList.contains('active') ? 'true' : 'false');
      btn.tabIndex = btn.classList.contains('active') ? 0 : -1;
      btn.addEventListener('click', () => activate(btn, false));
      btn.addEventListener('keydown', e => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const next = buttons[(i + (e.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length];
          activate(next, true);
        }
      });
    });
    /* Pre-select a tab from the page's platform when asked to */
    if (tabs.dataset.autoplatform !== undefined) {
      const ua = navigator.userAgent || '';
      const want = /Windows/i.test(ua) ? tabs.dataset.win
        : (/Android/i.test(ua) ? null : (/Linux|X11|CrOS/i.test(ua) ? tabs.dataset.linux : null));
      const btn = want && buttons.find(b => b.dataset.tab === want);
      if (btn) activate(btn, false);
    }
  });

  /* ── Carousel ── */
  document.querySelectorAll('.carousel').forEach(carousel => {
    const track = carousel.querySelector('.carousel-track');
    const slides = carousel.querySelectorAll('.carousel-slide');
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');
    const dotsContainer = carousel.querySelector('.carousel-dots');
    let current = 0;
    const total = slides.length;
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
      dot.addEventListener('click', () => goTo(i));
      dotsContainer.appendChild(dot);
    });
    const dots = dotsContainer.querySelectorAll('.carousel-dot');
    function goTo(index) {
      slides[current].querySelectorAll('video').forEach(v => v.pause());
      current = ((index % total) + total) % total;
      track.style.transform = 'translateX(-' + (current * 100) + '%)';
      dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }
    prevBtn.addEventListener('click', () => goTo(current - 1));
    nextBtn.addEventListener('click', () => goTo(current + 1));
    let autoplay = setInterval(() => goTo(current + 1), 6000);
    carousel.addEventListener('mouseenter', () => clearInterval(autoplay));
    carousel.addEventListener('mouseleave', () => {
      autoplay = setInterval(() => goTo(current + 1), 6000);
    });
    let startX = 0;
    carousel.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
    carousel.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) goTo(current + (dx > 0 ? -1 : 1));
    }, { passive: true });
  });

  /* ── Parallax on hero bg ── */
  const heroBg = document.querySelector('.hero-bg-img');
  if (heroBg) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y < window.innerHeight) {
        heroBg.style.transform = `translateY(${y * 0.3}px) scale(1.1)`;
      }
    }, { passive: true });
  }

  /* ── Interactive isometric cube architecture ── */
  const cubeGrid = document.getElementById('cubeGrid');
  if (cubeGrid) {
    const CUBE_SIZE = 48, COL_STEP = 90, ROW_STEP = 110;
    const cubesData = [
      { id:'code',      layer:'app',        col:-2.5, row:0, label:'Code',      name:'AbstractCode',      layerName:'Application',       href:'code.html',      desc:'A coding agent that runs durably on the gateway, with a terminal client and a browser client. Tool approvals, workspace files, streamed replies and automations.' },
      { id:'flow',      layer:'app',        col:-1.5, row:0, label:'Flow',      name:'AbstractFlow',      layerName:'Application',       href:'flow.html',      desc:'The visual workflow editor. Draw workflows in the browser, publish them to the gateway as portable .flow bundles.' },
      { id:'observer',  layer:'app',        col:-0.5, row:0, label:'Observer',  name:'AbstractObserver',  layerName:'Application',       href:'observer.html',  desc:'Watch runs live, replay the ledger step by step, and create and manage automations.' },
      { id:'assistant', layer:'app',        col:0.5,  row:0, label:'Assistant', name:'AbstractAssistant', layerName:'Application',       href:'assistant.html', desc:'A macOS menu-bar assistant with a palette, a voice mode, and your sessions and automations one key away.' },
      { id:'continuum', layer:'app',        col:1.5,  row:0, label:'Continuum', name:'AbstractContinuum', layerName:'Application',       href:'continuum.html', desc:'A board-first console for continuous development and deployment work.' },
      { id:'entity',    layer:'app',        col:2.5,  row:0, label:'Entity',    name:'AbstractEntity',    layerName:'Application',       href:'entity.html',    desc:'Create entities with a lasting memory of their own, talk with them, and read their diaries.' },
      { id:'gateway',   layer:'control',    col:0,    row:1, label:'Gateway',   name:'AbstractGateway',   layerName:'Control Plane',     href:'gateway.html',   desc:'The control plane: durable runs over HTTP and SSE, automations, the web and terminal consoles, the apps at /apps/<app>/, and multi-user auth.' },
      { id:'agent',     layer:'compose',    col:-0.5, row:2, label:'Agent',     name:'AbstractAgent',     layerName:'Composition',       href:'agent.html',     desc:'Agent patterns (ReAct, CodeAct, MemAct) built on AbstractRuntime and AbstractCore.' },
      { id:'flowrt',    layer:'compose',    col:0.5,  row:2, label:'Bundles',   name:'Workflow bundles',  layerName:'Composition',       href:'flow.html',      desc:'Portable .flow bundles, compiled and run durably by AbstractRuntime on the gateway.' },
      { id:'core',      layer:'foundation', col:-0.5, row:3, label:'Core',      name:'AbstractCore',      layerName:'Foundation',        href:'core.html',      desc:'One Python LLM API over ten provider types, local and cloud: tools, structured output, media, embeddings, an OpenAI-compatible server and a console.' },
      { id:'runtime',   layer:'foundation', col:0.5,  row:3, label:'Runtime',   name:'AbstractRuntime',   layerName:'Foundation',        href:'runtime.html',   desc:'Durable execution: interrupt, checkpoint, resume, with an append-only ledger. Runs automations and keeps a whole-message history window.' },
      { id:'voice',     layer:'plugin',     col:-1,   row:4, label:'Voice',     name:'AbstractVoice',     layerName:'Capability Plugin', href:'voice.html',     desc:'Text-to-speech, speech-to-text and voice cloning, local or remote, with engines that say why they cannot run.' },
      { id:'vision',    layer:'plugin',     col:0,    row:4, label:'Vision',    name:'AbstractVision',    layerName:'Capability Plugin', href:'vision.html',    desc:'Image generation, editing and upscaling, text-to-video and image-to-video, through MLX-Gen, Diffusers, stable-diffusion.cpp or OpenAI-compatible services.' },
      { id:'music',     layer:'plugin',     col:1,    row:4, label:'Music',     name:'AbstractMusic',     layerName:'Capability Plugin', href:'music.html',     desc:'Text-to-music and text-to-audio: ACE Music and ElevenLabs remotely, ACE-Step and Stable Audio locally.' },
      { id:'memory',    layer:'knowledge',  col:-0.5, row:5, label:'Memory',    name:'AbstractMemory',    layerName:'Knowledge',         href:'memory.html',    desc:'Durable, append-only agent memory: temporal triples, and a memory system that forms, recalls and consolidates records from use.' },
      { id:'semantics', layer:'knowledge',  col:0.5,  row:5, label:'Semantics', name:'AbstractSemantics', layerName:'Knowledge',         href:'semantics.html', desc:'The shared vocabulary: predicates, entity types and memory relations, with JSON Schema helpers.' },
    ];
    const layerColors = { app:'#34d399', control:'#22d3ee', compose:'#818cf8', foundation:'#6366f1', plugin:'#f472b6', knowledge:'#fbbf24' };

    cubesData.forEach(c => {
      const cx = c.col * COL_STEP, cy = c.row * ROW_STEP;
      const wrap = document.createElement('div');
      wrap.className = 'cube-wrap';
      wrap.dataset.id = c.id;
      wrap.dataset.layer = c.layer;
      wrap.style.cssText = '--size:'+CUBE_SIZE+'px;--tx:'+cx+'px;--ty:'+cy+'px;transform:translate('+cx+'px,'+cy+'px)';
      wrap.innerHTML = '<div class="cube"><div class="face top"></div><div class="face left"></div><div class="face right"></div></div>'
        + '<div class="cube-tooltip"><div class="tip-layer" style="color:'+layerColors[c.layer]+'">'+c.layerName+'</div>'
        + '<div class="tip-name">'+c.name+'</div><div class="tip-desc">'+c.desc+'</div></div>'
        + '<div class="cube-label">'+c.label+'</div>';
      wrap.setAttribute('role', 'listitem');
      wrap.tabIndex = 0;
      wrap.setAttribute('aria-label', c.name + ' (' + c.layerName + '): ' + c.desc);
      wrap.addEventListener('click', function(){ window.location.href = c.href; });
      wrap.addEventListener('keydown', function(e){ if (e.key === 'Enter') window.location.href = c.href; });
      cubeGrid.appendChild(wrap);
    });

    var layerLabels = [
      { row:0, text:'APPLICATIONS', color:'#34d399' },
      { row:1, text:'CONTROL PLANE', color:'#22d3ee' },
      { row:2, text:'COMPOSITION', color:'#818cf8' },
      { row:3, text:'FOUNDATION', color:'#6366f1' },
      { row:4, text:'PLUGINS', color:'#f472b6' },
      { row:5, text:'KNOWLEDGE', color:'#fbbf24' },
    ];
    layerLabels.forEach(function(l) {
      var el = document.createElement('div');
      el.className = 'layer-label';
      el.dataset.layer = ['app','control','compose','foundation','plugin','knowledge'][l.row];
      el.style.cssText = 'left:'+(3.3*COL_STEP)+'px;top:'+(l.row*ROW_STEP+14)+'px;color:'+l.color;
      el.textContent = l.text;
      cubeGrid.appendChild(el);
    });

    var cubeWraps = cubeGrid.querySelectorAll('.cube-wrap[data-id]');
    var cubeLabels = cubeGrid.querySelectorAll('.layer-label');
    function highlightCube(id) {
      var activeLayer = null;
      cubeWraps.forEach(function(w){ if(w.dataset.id===id) activeLayer=w.dataset.layer; });
      cubeWraps.forEach(function(w){
        w.classList.toggle('active', w.dataset.id===id);
        w.classList.toggle('dimmed', id && w.dataset.id!==id);
      });
      cubeLabels.forEach(function(l){ l.classList.toggle('highlight', l.dataset.layer===activeLayer); });
    }
    function clearCubeHighlight() {
      cubeWraps.forEach(function(w){ w.classList.remove('active','dimmed'); });
      cubeLabels.forEach(function(l){ l.classList.remove('highlight'); });
    }
    cubeWraps.forEach(function(w){
      w.addEventListener('mouseenter', function(){ highlightCube(w.dataset.id); });
      w.addEventListener('mouseleave', clearCubeHighlight);
      w.addEventListener('focus', function(){ highlightCube(w.dataset.id); });
      w.addEventListener('blur', clearCubeHighlight);
    });
  }

  /* ── Active nav link highlighting ── */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id);
        });
      }
    });
  }, { threshold: 0.3, rootMargin: '-80px 0px -50% 0px' });
  sections.forEach(s => navObserver.observe(s));

});
