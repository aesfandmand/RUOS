// Signature motion B (design model §7): the hero slider. Native scroll-snap
// does the swiping — no library, no autoplay racing the reader — and this
// only keeps the dots in step and makes them a real control.

const stage = document.querySelector(".p-hero-stage");
if (stage) {
  const slides = [...stage.querySelectorAll(".p-hero-slide")];
  const dots = [...document.querySelectorAll(".p-hero-dots button")];

  const mark = (index) => dots.forEach((dot, dotIndex) => {
    const on = dotIndex === index;
    dot.classList.toggle("is-active", on);
    dot.setAttribute("aria-current", on ? "true" : "false");
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) mark(slides.indexOf(entry.target));
    });
  }, { root: stage, threshold: 0.6 });
  slides.forEach((slide) => observer.observe(slide));

  dots.forEach((dot, index) =>
    dot.addEventListener("click", () => {
      slides[index]?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }),
  );
}
