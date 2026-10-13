// §22: the desktop hero is one viewport tall, minus a deliberate sliver of the
// next section. Browser chrome makes 100svh unreliable on some setups, so the
// measured header height is fed back as a custom property rather than assumed.
(() => {
  const hero = document.querySelector('[data-block="hub-hero"]');
  if (!hero) return;
  const header = document.querySelector(".site-header");
  if (!header) return;
  const sync = () => {
    const h = Math.round(header.getBoundingClientRect().height);
    if (h > 0) hero.style.setProperty("--header", `${h}px`);
  };
  sync();
  window.addEventListener("resize", sync, { passive: true });
})();

// The light field. The pointer is a lamp; until it arrives, the lamp wanders
// on its own so the hero is never a still picture. Pointer devices only, and
// nothing here carries meaning — it is decoration over an aria-hidden span.
(() => {
  const field = document.querySelector(".hub-hero-field");
  if (!field) return;
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const hero = field.closest('[data-block="hub-hero"]');
  let tx = 50, ty = 42;   // target, in percent of the hero box
  let lx = 50, ly = 42;   // where the light has got to
  let pointerSeen = false;
  let t0 = performance.now();

  hero.addEventListener("pointermove", (event) => {
    if (event.pointerType !== "mouse") return;
    const box = hero.getBoundingClientRect();
    tx = ((event.clientX - box.left) / box.width) * 100;
    ty = ((event.clientY - box.top) / box.height) * 100;
    pointerSeen = true;
  }, { passive: true });

  hero.addEventListener("pointerleave", () => { pointerSeen = false; });

  const frame = (now) => {
    if (!pointerSeen) {
      // a slow lissajous wander, so the idle state still breathes
      const s = (now - t0) / 1000;
      tx = 50 + Math.sin(s * 0.32) * 26;
      ty = 44 + Math.sin(s * 0.21 + 1.1) * 16;
    }
    lx += (tx - lx) * 0.07;
    ly += (ty - ly) * 0.07;
    field.style.setProperty("--lx", `${lx.toFixed(2)}%`);
    field.style.setProperty("--ly", `${ly.toFixed(2)}%`);
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
})();
