// The cursor arc — design model §21/§22.
// The shape says what is possible in this part of the page, and because it
// changes on the way down, it draws an arc of its own. It is decoration: it
// adds no affordance, removes nothing, and never runs on a touch device.
//
// Two trackers, two speeds. The dot is pinned to the pointer; the glass ring
// eases toward it and arrives a beat later. That lag is the whole reason the
// thing reads as a material instead of a sprite following the mouse.
(() => {
  const host = document.querySelector('[data-block="page-cursor"]');
  if (!host) return;
  const layer = host.querySelector(".page-cursor");
  const dot = host.querySelector(".page-cursor-dot");
  const label = host.querySelector(".page-cursor-label");
  if (!layer || !dot || !label) return;

  const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  if (!fine.matches) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  const map = [...host.querySelectorAll(".page-cursor-map")].map((node) => ({
    selector: node.dataset.selector || "",
    state: node.dataset.state || "default",
    label: node.dataset.label || "",
  })).filter((entry) => entry.selector);
  if (!map.length) return;

  let px = 0;      // pointer, exact
  let py = 0;
  let rx = 0;      // ring, eased
  let ry = 0;
  let live = false;
  let running = false;
  let shiftTimer = 0;

  const tick = () => {
    // 0.18 is slow enough to be felt and fast enough never to feel broken.
    const ease = reduced.matches ? 1 : 0.18;
    rx += (px - rx) * ease;
    ry += (py - ry) * ease;
    dot.style.setProperty("--dx", `${px}px`);
    dot.style.setProperty("--dy", `${py}px`);
    layer.style.setProperty("--cx", `${rx}px`);
    layer.style.setProperty("--cy", `${ry}px`);
    if (Math.abs(px - rx) < 0.1 && Math.abs(py - ry) < 0.1) {
      running = false;
      return;
    }
    requestAnimationFrame(tick);
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
    px = event.clientX;
    py = event.clientY;
    if (!live) {
      live = true;
      rx = px;
      ry = py;
      layer.classList.add("is-live");
      dot.classList.add("is-live");
    }
    start();

    const target = event.target instanceof Element ? event.target : null;
    const hit = target ? resolve(target) : null;
    const state = hit ? hit.state : "default";
    if (layer.dataset.state !== state) {
      layer.dataset.state = state;
      label.textContent = hit ? hit.label : "";
      // the beat: a short overshoot on arrival, then settle
      layer.classList.add("is-shift");
      clearTimeout(shiftTimer);
      shiftTimer = setTimeout(() => layer.classList.remove("is-shift"), 180);
    }
  }, { passive: true });

  const hide = () => {
    live = false;
    layer.classList.remove("is-live");
    dot.classList.remove("is-live");
  };
  document.addEventListener("pointerleave", hide);
  window.addEventListener("blur", hide);
})();
