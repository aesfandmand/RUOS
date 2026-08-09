import { animate, inView, stagger } from "./motion.min.mjs";

document.querySelectorAll(".structure-spec-list").forEach((list) => {
  const rows = [...list.querySelectorAll(".structure-spec-row")];
  if (!rows.length) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  rows.forEach((row) => { row.style.opacity = "0"; });
  inView(list, () => {
    animate(rows, { opacity: [0, 1], y: [12, 0] },
      { duration: 0.5, delay: stagger(0.08), easing: [0.16, 1, 0.3, 1] });
  }, { amount: 0.3 });
});
