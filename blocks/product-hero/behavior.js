// The opening scene (design model §7 + §15). Three things move here: the
// headline arrives word by word, the image wipes up and then drifts, and the
// index and next-slide preview track the rail — the pattern from the owner's
// slider reference, where what comes next is always named on screen.

const hero = document.querySelector(".p-hero");
if (hero) {
  const heading = hero.querySelector("h1[data-split]");
  if (heading) {
    // split into words rather than characters: Persian is cursive, and
    // splitting inside a word would break the joins.
    heading.innerHTML = heading.textContent.trim().split(/\s+/)
      .map((word, index) => `<span class="w" style="--w:${index}">${word}</span>`)
      .join(" ");
    requestAnimationFrame(() => heading.classList.add("is-split"));
  }

  const stage = hero.querySelector(".p-hero-stage");
  const slides = [...hero.querySelectorAll(".p-hero-slide")];
  const dots = [...hero.querySelectorAll(".p-hero-dots button")];
  const index = hero.querySelector(".p-hero-index b");
  const nextButton = hero.querySelector(".p-hero-next");
  const nextLabel = hero.querySelector(".p-hero-next-label");
  const fa = (value) => new Intl.NumberFormat("fa-IR", { minimumIntegerDigits: 2, useGrouping: false }).format(value);

  let current = 0;
  const mark = (position) => {
    current = position;
    dots.forEach((dot, dotIndex) => {
      const on = dotIndex === position;
      dot.classList.toggle("is-active", on);
      dot.setAttribute("aria-current", on ? "true" : "false");
    });
    if (index) index.textContent = fa(position + 1);
    const upcoming = slides[(position + 1) % slides.length];
    if (nextLabel && upcoming) nextLabel.textContent = upcoming.dataset.caption || "";
  };

  const go = (position) => slides[position]?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });

  if (stage) {
    const watcher = new IntersectionObserver((entries) => {
      entries.forEach((entry) => { if (entry.isIntersecting) mark(slides.indexOf(entry.target)); });
    }, { root: stage, threshold: 0.6 });
    slides.forEach((slide) => watcher.observe(slide));
  }
  dots.forEach((dot, position) => dot.addEventListener("click", () => go(position)));
  nextButton?.addEventListener("click", () => go((current + 1) % slides.length));
  mark(0);
}
