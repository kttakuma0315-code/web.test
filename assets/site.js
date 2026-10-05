(() => {
  const root = document.documentElement;
  root.classList.add('js');
  const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('#navigation');
  const activeAnimations = new Set();
  let observer;
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
  }
  function initializeMotion() {
    resetMotion();
    queueProgress();
    if (motionPreference.matches) return;
    const main = document.querySelector('#main');
    // The page itself always remains opaque, including during navigation.
    animate(main, [{ transform: 'translateY(6px)' }, { transform: 'translateY(0)' }], { duration: 420 });
    document.querySelectorAll('.hero-copy > *').forEach((element, index) => {
      animate(element, [{ transform: 'translateY(10px)' }, { transform: 'translateY(0)' }], { delay: Math.min(index * 55, 220), fill: 'backwards' });
    });
    animate(document.querySelector('.hero-art img'), [
      { transform: 'scale(1.025)' },
      { transform: 'scale(1)' },
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
    ].join(',')).forEach(element => {
      // Already visible content must never disappear and restart its entrance.
      const rect = element.getBoundingClientRect();
      if (rect.top >= window.innerHeight) observer.observe(element);
    });
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

  // Native links avoid any blank intermediate document. Supporting browsers use
  // the CSS View Transition; other browsers navigate normally without a fade-out.
  window.addEventListener('pageshow', event => {
    if (event.persisted) initializeMotion();
  });
  window.addEventListener('kuromugi:pagechange', initializeMotion);
  motionPreference.addEventListener('change', initializeMotion);
  initializeMotion();
})();
