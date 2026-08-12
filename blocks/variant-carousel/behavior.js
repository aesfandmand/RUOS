// Signature motion C (design model §8.1): depth carousel. The card nearest
// the rail's centre is dominant; its neighbours sit back and turn slightly.
// --near is 0 at the centre and 1 at a card-width away; --side is which side
// it is on, so the two neighbours lean in opposite directions.

document.querySelectorAll(".var-track").forEach((track) => {
  const cards = [...track.children];
  if (!cards.length) return;
  let ticking = 0;

  const settle = () => {
    ticking = 0;
    const rail = track.getBoundingClientRect();
    const centre = rail.left + rail.width / 2;
    cards.forEach((card) => {
      const box = card.getBoundingClientRect();
      const offset = (box.left + box.width / 2 - centre) / box.width;
      card.style.setProperty("--near", String(Math.min(1, Math.abs(offset))));
      card.style.setProperty("--side", String(Math.sign(offset) || 0));
    });
  };

  track.addEventListener("scroll", () => {
    if (!ticking) ticking = requestAnimationFrame(settle);
  }, { passive: true });
  addEventListener("resize", settle);
  settle();
  requestAnimationFrame(settle);
});
