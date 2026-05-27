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
      e.preventDefault();
      const el = document.querySelector(a.getAttribute('href'));
      if (el) {
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
      const text = code.textContent.trim();
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
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    links.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => links.classList.remove('open'));
    });
  }

  /* ── Image lightbox ── */
  document.querySelectorAll('.showcase-img img, .gallery-item img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      const overlay = document.createElement('div');
      overlay.className = 'lightbox-overlay';
      overlay.innerHTML = `<img src="${img.src}" alt="${img.alt || ''}" />`;
      overlay.addEventListener('click', () => overlay.remove());
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', esc); }
      });
      document.body.appendChild(overlay);
    });
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
