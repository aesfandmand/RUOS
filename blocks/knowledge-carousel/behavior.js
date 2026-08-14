// Prev/next buttons and dots per group, desktop only (owner's report,
// 2026-08-14): the rail is a bare scroll container with the native
// scrollbar hidden, so a mouse user had no visible way to move it or any
// sense of position within it. Touch/swipe already works and is untouched.

document.querySelectorAll(".kn-group").forEach((group) => {
  const track = group.querySelector(".kn-track");
  const cards = track ? [...track.children] : [];
  if (!track || !cards.length) return;
  let ticking = 0;

  const dotsHost = group.querySelector(".kn-dots");
  const dots = cards.map((_, index) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", `مورد ${index + 1}`);
    dot.addEventListener("click", () => {
      cards[index].scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    });
    dotsHost?.appendChild(dot);
    return dot;
  });

  const settle = () => {
    ticking = 0;
    const railBox = track.getBoundingClientRect();
    const centre = railBox.left + railBox.width / 2;
    let closestIndex = 0;
    let closestDistance = Infinity;
    cards.forEach((card, index) => {
      const box = card.getBoundingClientRect();
      const distance = Math.abs(box.left + box.width / 2 - centre);
      if (distance < closestDistance) { closestDistance = distance; closestIndex = index; }
    });
    dots.forEach((dot, index) => dot.classList.toggle("is-active", index === closestIndex));
  };

  track.addEventListener("scroll", () => {
    if (!ticking) ticking = requestAnimationFrame(settle);
  }, { passive: true });
  addEventListener("resize", settle);
  settle();

  group.querySelector(".kn-prev")?.addEventListener("click", () => {
    track.scrollBy({ left: track.clientWidth * (document.dir === "rtl" ? 1 : -1) * 0.86, behavior: "smooth" });
  });
  group.querySelector(".kn-next")?.addEventListener("click", () => {
    track.scrollBy({ left: track.clientWidth * (document.dir === "rtl" ? -1 : 1) * 0.86, behavior: "smooth" });
  });
});
