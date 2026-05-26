document.addEventListener('DOMContentLoaded',()=>{
  /* Nav scroll */
  const nav=document.querySelector('.nav');
  window.addEventListener('scroll',()=>{
    nav.classList.toggle('scrolled',window.scrollY>50);
  },{passive:true});

  /* Smooth scroll for anchors */
  document.querySelectorAll('a[href^="#"]').forEach(a=>{
    a.addEventListener('click',e=>{
      e.preventDefault();
      const t=document.querySelector(a.getAttribute('href'));
      if(t) t.scrollIntoView({behavior:'smooth',block:'start'});
    });
  });

  /* Scroll reveal */
  const io=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add('visible');io.unobserve(e.target);}
    });
  },{threshold:0.1,rootMargin:'0px 0px -60px 0px'});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

  /* Mobile menu toggle */
  const toggle=document.querySelector('.mobile-toggle');
  const links=document.querySelector('.nav-links');
  if(toggle){
    toggle.addEventListener('click',()=>{
      links.style.display=links.style.display==='flex'?'none':'flex';
      links.style.flexDirection='column';
      links.style.position='absolute';
      links.style.top='64px';
      links.style.left='0';
      links.style.right='0';
      links.style.background='rgba(10,10,15,.98)';
      links.style.padding='1rem 2rem';
      links.style.borderBottom='1px solid var(--border)';
    });
  }

  /* Copy code button */
  document.querySelectorAll('.code-block').forEach(block=>{
    const btn=document.createElement('button');
    btn.textContent='Copy';
    btn.style.cssText='position:absolute;top:.5rem;right:.5rem;padding:.25rem .6rem;font-size:.7rem;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;color:var(--text-muted);cursor:pointer;font-family:var(--font);transition:all .2s';
    btn.addEventListener('click',()=>{
      const code=block.textContent.replace('Copy','').trim();
      navigator.clipboard.writeText(code).then(()=>{
        btn.textContent='Copied!';
        setTimeout(()=>btn.textContent='Copy',2000);
      });
    });
    block.appendChild(btn);
  });

  /* Architecture block tooltips */
  document.querySelectorAll('.arch-block[data-tip]').forEach(b=>{
    b.title=b.dataset.tip;
  });
});
