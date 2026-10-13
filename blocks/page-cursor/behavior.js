// The cursor arc — design model §21.
// The shape says what is possible in this part of the page, and because it
// changes on the way down, it draws an arc of its own. It is decoration: it
// adds no affordance, removes nothing, and never runs on a touch device.
//
// Amended 2026-10-13: the layer now eases toward the pointer instead of being
// pinned to it. The few frames of lag are the whole difference between a dot
// stuck to the mouse and something that feels like it has weight.
(() => {
  const host = document.querySelector('[data-block="page-cursor"]');
  if (!host) return;
  const layer = host.querySelector(".page-cursor");
  const label = host.querySelector(".page-cursor-label");
  if (!layer || !label) return;

  const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  if (!fine.matches) return;
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const map = [...host.querySelectorAll(".page-cursor-map")].map((node) => ({
    selector: node.dataset.selector || "",
    state: node.dataset.state || "default",
    label: node.dataset.label || "",
  })).filter((entry) => entry.selector);
  if (!map.length) return;

  let tx = 0, ty = 0;   // where the pointer is
  let cx = 0, cy = 0;   // where the layer has got to
  let live = false, running = false;

  const tick = () => {
    // A straight lerp: fast enough to stay with a quick flick, slow enough to
    // read as weight. Reduced motion skips the easing entirely.
    const k = calm ? 1 : 0.18;
    cx += (tx - cx) * k;
    cy += (ty - cy) * k;
    layer.style.setProperty("--cx", `${cx.toFixed(1)}px`);
    layer.style.setProperty("--cy", `${cy.toFixed(1)}px`);
    if (Math.abs(tx - cx) > 0.1 || Math.abs(ty - cy) > 0.1) {
      requestAnimationFrame(tick);
    } else {
      running = false;
    }
  };

  const start = () => {
    if (running) return;
    running = true;
    requestAnimationFrame(tick);
  };

  const resolve = (target) => {
    for (const entry of map) {
      let match = null;
      try {
        match = target.closest(entry.selector);
      } catch {
        match = null; // a bad selector in the data must not take the page down
      }
      if (match) return entry;
    }
    return null;
  };

  document.addEventListener("pointermove", (event) => {
    if (event.pointerType !== "mouse") return;
    tx = event.clientX;
    ty = event.clientY;
    if (!live) {
      live = true;
      cx = tx; cy = ty;           // no flight in from the corner on first move
      layer.classList.add("is-live");
    }
    start();

    const target = event.target instanceof Element ? event.target : null;
    const hit = target ? resolve(target) : null;
    const state = hit ? hit.state : "default";
    if (layer.dataset.state !== state) {
      layer.dataset.state = state;
      label.textContent = hit ? hit.label : "";
    }
  }, { passive: true });

  document.addEventListener("pointerleave", () => {
    live = false;
    layer.classList.remove("is-live");
  });
})();
