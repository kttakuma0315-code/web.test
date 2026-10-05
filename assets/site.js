(() => {
  const root = document.documentElement;
  root.classList.add('js');
  const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('#navigation');
  const activeAnimations = new Set();
  let observer;
  let navigating = false;
  let scrollFrame = 0;

  function closeNav() {
    toggle?.setAttribute('aria-expanded', 'false');
    nav?.classList.remove('is-open');
  }
  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav?.classList.toggle('is-open', open);
  });
  nav?.addEventListener('click', event => {
    if (event.target.closest('a')) closeNav();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      closeNav();
      toggle.focus();
    }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.site-header')) closeNav();
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1000) closeNav();
    queueProgress();
  });

  // Content stays readable if an animation or observer is unavailable.
  function animate(element, keyframes, options = {}) {
    if (!element || motionPreference.matches || typeof element.animate !== 'function') return null;
    const animation = element.animate(keyframes, {
      duration: 780,
      easing: 'cubic-bezier(.22, 1, .36, 1)',
      ...options,
    });
    activeAnimations.add(animation);
    animation.finished.then(
      () => activeAnimations.delete(animation),
      () => activeAnimations.delete(animation),
    );
    return animation;
  }
  function reveal(element, delay = 0) {
    return animate(element, [
      { opacity: 0, transform: 'translateY(18px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ], { delay, fill: 'backwards' });
  }
  function resetMotion() {
    observer?.disconnect();
    activeAnimations.forEach(animation => animation.cancel());
    activeAnimations.clear();
    navigating = false;
  }
  function initializeMotion() {
    resetMotion();
    queueProgress();
    if (motionPreference.matches) return;
    const main = document.querySelector('#main');
    animate(main, [{ opacity: 0 }, { opacity: 1 }], { duration: 520 });
    document.querySelectorAll('.hero-copy > *').forEach((element, index) => {
      reveal(element, Math.min(index * 55, 220));
    });
    animate(document.querySelector('.hero-art img'), [
      { opacity: 0, transform: 'scale(1.025)' },
      { opacity: 1, transform: 'scale(1)' },
    ], { duration: 1150 });
    if (!('IntersectionObserver' in window)) return;
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const group = Array.from(entry.target.parentElement.children);
        reveal(entry.target, Math.min(group.indexOf(entry.target) * 65, 130));
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' });
    document.querySelectorAll([
      '.intro > *:not(.intro-side)', '.split > *', '.section-heading',
      '.time-card', '.three-cards > article', '.news-row', '.visit-item',
      '.reservation-box', '.faq-list > details', '.page-head > *',
    ].join(',')).forEach(element => observer.observe(element));
  }

  const progress = document.createElement('div');
  progress.className = 'reading-progress';
  progress.setAttribute('aria-hidden', 'true');
  document.body.append(progress);
  function updateProgress() {
    scrollFrame = 0;
    const distance = root.scrollHeight - window.innerHeight;
    const fraction = distance > 0 ? Math.min(1, Math.max(0, window.scrollY / distance)) : 0;
    progress.style.transform = `scaleX(${fraction})`;
  }
  function queueProgress() {
    if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateProgress);
  }
  window.addEventListener('scroll', queueProgress, { passive: true });
  window.addEventListener('load', queueProgress, { once: true });

  // Preserve native behavior for anchors, calls, external links and new tabs.
  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href]');
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const href = link.getAttribute('href');
    const previewPage = /^#page-[a-z]+$/.test(href);
    if (href.startsWith('#') && !previewPage) return;
    let destination;
    try { destination = new URL(link.href, window.location.href); } catch { return; }
    if (!previewPage && (
      destination.origin !== window.location.origin ||
      !['http:', 'https:', 'file:'].includes(destination.protocol) ||
      !destination.pathname.endsWith('.html') ||
      destination.pathname === window.location.pathname
    )) return;
    if (previewPage && destination.hash === window.location.hash) return;
    if (motionPreference.matches || typeof document.querySelector('#main')?.animate !== 'function') return;
    event.preventDefault();
    if (navigating) return;
    navigating = true;
    const main = document.querySelector('#main');
    animate(main, [{ opacity: 1 }, { opacity: 0 }], {
      duration: 160, easing: 'ease-out', fill: 'forwards',
    });
    // A short fixed fallback guarantees navigation even if animation is cancelled.
    window.setTimeout(() => window.location.assign(destination.href), 170);
  });
  window.addEventListener('pageshow', initializeMotion);
  window.addEventListener('kuromugi:pagechange', initializeMotion);
  motionPreference.addEventListener('change', initializeMotion);
  initializeMotion();
})();
