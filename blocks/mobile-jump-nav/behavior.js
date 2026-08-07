/* mobile-jump-nav — marks the entry whose section currently owns the viewport. */
document.querySelectorAll('[data-block="mobile-jump-nav"]').forEach((nav) => {
  const links = [...nav.querySelectorAll('a')];
  const targets = links
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);
  if (!targets.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((link) => {
        link.classList.toggle('is-active', link.getAttribute('href') === `#${entry.target.id}`);
      });
    });
  }, { rootMargin: '-35% 0px -55%' });

  targets.forEach((target) => observer.observe(target));
});
