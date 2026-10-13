// kinetic-oversized-type — design model §21.
// Drives --kin from 0 to 1 as the section crosses the viewport. Everything here
// is additive: the heading is already in place and readable before this runs,
// and if it never runs at all, the CSS falls back to --kin:1, which is rest.
(() => {
  const sections = [...document.querySelectorAll('[data-block="golden-line"]')];
  if (!sections.length) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const tracks = sections
    .map((section) => ({ section, track: section.querySelector(".golden-line-track") }))
    .filter((entry) => entry.track);
  if (!tracks.length) return;

  let frame = 0;

  const update = () => {
    frame = 0;
    const viewport = window.innerHeight || 1;
    for (const { section, track } of tracks) {
      const box = section.getBoundingClientRect();
      const span = viewport + box.height;
      // 0 while the section is still below the fold; 1 once it has risen past
      // the middle of the screen. Clamped, so it never overshoots either end.
      const raw = span ? (viewport - box.top) / span : 1;
      const kin = Math.min(1, Math.max(0, raw * 1.9));
      track.style.setProperty("--kin", kin.toFixed(4));
    }
  };

  const schedule = () => {
    if (frame) return;
    frame = requestAnimationFrame(update);
  };

  update();
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule, { passive: true });
})();
