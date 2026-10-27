// portfolio-accordion — §21 horizontal-accordion. Click, focus or the arrow
// keys move the open panel; on desktop the panel under the pointer opens
// after a short dwell, so a sweep across the row does not thrash it.
(() => {
  document.querySelectorAll('[data-block="portfolio-accordion"]').forEach((section) => {
    const panels = [...section.querySelectorAll(".pfa-panel")];
    if (panels.length < 2) return;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    let active = 0;
    let dwell = 0;

    const open = (i) => {
      active = (i + panels.length) % panels.length;
      panels.forEach((p, k) => {
        const on = k === active;
        p.classList.toggle("is-active", on);
        p.querySelector(".pfa-tab")?.setAttribute("aria-expanded", String(on));
        p.querySelector(".pfa-open")?.toggleAttribute("inert", !on);
      });
    };

    panels.forEach((p, i) => {
      const tab = p.querySelector(".pfa-tab");
      tab?.addEventListener("click", () => open(i));
      tab?.addEventListener("keydown", (e) => {
        if (e.key === "ArrowLeft") { open(i + 1); panels[active].querySelector(".pfa-all")?.focus(); }
        if (e.key === "ArrowRight") { open(i - 1); panels[active].querySelector(".pfa-all")?.focus(); }
      });
      if (fine) {
        p.addEventListener("pointerenter", () => { clearTimeout(dwell); dwell = setTimeout(() => open(i), 260); });
        p.addEventListener("pointerleave", () => clearTimeout(dwell));
      }
    });

    section.classList.add("is-ready");
    open(0);
  });
})();
