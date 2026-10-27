// portfolio-hero — §21 active-card-becomes-hero, in the straboard hero idiom.
// The headline arrives word by word; the panel wipes up and drifts; swiping,
// the dots or the next-sample card advance it, and the index, the next card
// and the sample plate follow. Fails open: without script the first sample
// and its plate are shown and the panel is a plain swipeable row.
(() => {
  const hero = document.querySelector('[data-block="portfolio-hero"]');
  if (!hero) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // §22: the measured header height feeds the one-viewport rule.
  const header = document.querySelector(".site-header");
  const syncHeader = () => {
    const h = header ? Math.round(header.getBoundingClientRect().height) : 0;
    if (h > 0) hero.style.setProperty("--header", `${h}px`);
  };
  syncHeader();
  addEventListener("resize", syncHeader, { passive: true });

  // Word-by-word headline (Persian is cursive: never split inside a word).
  const heading = hero.querySelector("h1[data-split]");
  if (heading && !reduce) {
    heading.innerHTML = heading.textContent.trim().split(/\s+/)
      .map((word, i) => `<span class="w" style="--w:${i}">${word}</span>`).join(" ");
    requestAnimationFrame(() => heading.classList.add("is-split"));
  }

  const stage = hero.querySelector(".pf-stage");
  const slides = [...hero.querySelectorAll(".pf-slide")];
  const dots = [...hero.querySelectorAll(".pf-dots button")];
  const plates = [...hero.querySelectorAll(".pf-plate")];
  const index = hero.querySelector(".pf-index b");
  const next = hero.querySelector(".pf-next");
  const nextTitle = hero.querySelector(".pf-next-title");
  const nextThumb = hero.querySelector(".pf-next-thumb");
  const fa = (v) => new Intl.NumberFormat("fa-IR", { minimumIntegerDigits: 2, useGrouping: false }).format(v);
  let current = -1;

  const mark = (pos) => {
    if (pos === current) return;
    current = pos;
    dots.forEach((d, i) => { d.classList.toggle("is-active", i === pos); d.setAttribute("aria-current", String(i === pos)); });
    plates.forEach((p, i) => p.classList.toggle("is-active", i === pos));
    slides.forEach((s, i) => {
      const v = s.querySelector("video");
      if (v) i === pos && !reduce ? v.play().catch(() => {}) : v.pause();
    });
    if (index) index.textContent = fa(pos + 1);
    const up = slides[(pos + 1) % slides.length];
    if (up) {
      if (nextTitle) nextTitle.textContent = up.dataset.title || "";
      if (nextThumb) nextThumb.style.backgroundImage = up.dataset.thumb ? `url("${up.dataset.thumb}")` : "";
    }
  };

  const go = (pos) => {
    const target = slides[(pos + slides.length) % slides.length];
    if (!target) return;
    stage.scrollTo({ left: target.offsetLeft - (stage.clientWidth - target.clientWidth) / 2,
                     behavior: reduce ? "auto" : "smooth" });
  };

  // Which slide is centred decides everything else.
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) mark(slides.indexOf(e.target)); });
  }, { root: stage, threshold: 0.6 });
  slides.forEach((s) => io.observe(s));

  dots.forEach((d, i) => d.addEventListener("click", () => { stop(); go(i); }));
  next?.addEventListener("click", () => { stop(); go(current + 1); });
  stage.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { stop(); go(current + 1); }
    if (e.key === "ArrowRight") { stop(); go(current - 1); }
  });
  stage.addEventListener("pointerdown", () => stop(), { passive: true });

  // Self-advance until the visitor takes over; never with reduced motion,
  // never off screen.
  let timer = 0;
  let taken = false;
  function stop() { taken = true; clearInterval(timer); }
  const run = () => { if (!reduce && !taken) timer = setInterval(() => go(current + 1), 6500); };
  new IntersectionObserver(([e]) => { clearInterval(timer); if (e.isIntersecting) run(); }, { threshold: 0.3 }).observe(hero);

  // Depth on scroll (§16 motion floor): the panel drifts slower than the page.
  if (!reduce) {
    let ticking = 0;
    const drift = () => {
      ticking = 0;
      const y = Math.min(window.scrollY, 420);
      stage.style.setProperty("--drift", `${y * 0.12}px`);
      stage.style.setProperty("--zoom", String(1 + Math.min(y, 300) * 0.00016));
    };
    addEventListener("scroll", () => { if (!ticking) ticking = requestAnimationFrame(drift); }, { passive: true });
  }

  // Copy this view's link — the scout sends it to their manager.
  const share = hero.querySelector(".pf-ghost");
  share?.addEventListener("click", async () => {
    const label = share.querySelector("span");
    const before = label.textContent;
    try { await navigator.clipboard.writeText(location.href); }
    catch { const t = document.createElement("textarea"); t.value = location.href; document.body.append(t);
            t.select(); document.execCommand("copy"); t.remove(); }
    share.classList.add("is-done");
    label.textContent = share.dataset.done || before;
    setTimeout(() => { share.classList.remove("is-done"); label.textContent = before; }, 2400);
  });

  hero.classList.add("is-ready");
  mark(0);
})();
