// The cursor arc — design model §21.
// The shape says what is possible in this part of the page, and because it
// changes on the way down, it draws an arc of its own. It is decoration: it
// adds no affordance, removes nothing, and never runs on a touch device.
(() => {
  const host = document.querySelector('[data-block="page-cursor"]');
  if (!host) return;
  const layer = host.querySelector(".page-cursor");
  const ring = host.querySelector(".page-cursor-ring");
  const label = host.querySelector(".page-cursor-label");
  if (!layer || !ring || !label) return;

  const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  if (!fine.matches) return;

  const map = [...host.querySelectorAll(".page-cursor-map")].map((node) => ({
    selector: node.dataset.selector || "",
    state: node.dataset.state || "default",
    label: node.dataset.label || "",
  })).filter((entry) => entry.selector);
  if (!map.length) return;

  let x = 0;
  let y = 0;
  let live = false;
  let frame = 0;

  const paint = () => {
    frame = 0;
    layer.style.setProperty("--cx", `${x}px`);
    layer.style.setProperty("--cy", `${y}px`);
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
    x = event.clientX;
    y = event.clientY;
    if (!live) {
      live = true;
      layer.classList.add("is-live");
    }
    if (!frame) frame = requestAnimationFrame(paint);

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
