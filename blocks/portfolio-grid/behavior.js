// portfolio-grid — two-level filter (family, then final service), a live
// count, an address that can be sent on, and skeleton-to-content (§21).
// Fails open: with no script every card is visible, every service chip is a
// real link to its own view, and the wide cells come from nth-child.
(() => {
  document.querySelectorAll('[data-block="portfolio-grid"]').forEach((section) => {
    const grid = section.querySelector(".pf-grid");
    const cards = [...section.querySelectorAll(".pf-card")];
    const famChips = [...section.querySelectorAll(".pf-chip[data-family]:not(.pf-chip--svc)")];
    const svcChips = [...section.querySelectorAll(".pf-chip--svc")];
    const countEl = section.querySelector("[data-pf-count]");
    const empty = section.querySelector(".pf-empty");
    const more = section.querySelector(".pf-more");
    const base = section.dataset.viewBase || "";
    const hub = section.dataset.hub || "";
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const BATCH = 12;
    const fa = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
    let family = "all";
    let service = "";
    let shown = BATCH;

    grid.classList.add("is-js");

    const render = ({ skeleton = true } = {}) => {
      const match = cards.filter((c) =>
        (family === "all" || c.dataset.family === family) && (!service || c.dataset.service === service));
      let visible = 0;
      cards.forEach((c) => {
        const on = match.includes(c) && match.indexOf(c) < shown;
        c.hidden = !on;
        c.classList.remove("is-wide");
        if (on) { if (visible % 5 === 0) c.classList.add("is-wide"); visible += 1; c.classList.add("is-in"); }
      });
      if (countEl) countEl.textContent = fa(match.length);
      section.querySelector(".pf-filter")?.classList.toggle("is-all", family === "all");
      if (empty) empty.hidden = match.length > 0;
      if (more) more.hidden = match.length <= shown;
      famChips.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.family === family)));
      svcChips.forEach((b) => {
        b.hidden = family !== "all" && b.dataset.family !== family;
        b.setAttribute("aria-pressed", String(b.dataset.service === service));
      });
      if (skeleton && !reduce) {
        grid.classList.add("is-loading");
        setTimeout(() => grid.classList.remove("is-loading"), 280);
      }
    };

    const writeAddress = () => {
      const target = service ? `${base}${service}/` : hub;
      if (target && window.location.pathname !== target && /^https?:/.test(window.location.protocol)) {
        try { history.replaceState({ family, service }, "", target); } catch { /* file:// preview */ }
      }
    };

    famChips.forEach((b) => b.addEventListener("click", () => {
      family = b.dataset.family; service = ""; shown = BATCH; render(); writeAddress();
    }));
    svcChips.forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault();
      const same = service === a.dataset.service;
      service = same ? "" : a.dataset.service;
      family = same ? family : a.dataset.family;
      shown = BATCH; render(); writeAddress();
    }));
    more?.addEventListener("click", () => { shown += BATCH; render({ skeleton: false }); });

    // A view link (/portfolio/service/<slug>/) opens on its service.
    const fromPath = window.location.pathname.startsWith(base)
      ? window.location.pathname.slice(base.length).replace(/\/$/, "") : "";
    const initial = fromPath || section.dataset.initial || "";
    const chip = svcChips.find((a) => a.dataset.service === initial);
    if (chip) { service = initial; family = chip.dataset.family; }
    render({ skeleton: false });

    // Play a card's motion cover only while it is on screen.
    if (!reduce && "IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => entries.forEach((en) => {
        const v = en.target.querySelector("video");
        if (v) en.isIntersecting ? v.play().catch(() => {}) : v.pause();
      }), { threshold: 0.4 });
      cards.forEach((c) => c.querySelector("video") && io.observe(c));
    }
  });
})();
