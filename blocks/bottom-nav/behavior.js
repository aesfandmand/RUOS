// Mobile bottom nav: position the floating "liquid" bubble above whichever
// item is active. Geometry is measured rather than hard-coded so the bar
// works with any number of entries and any bar width.

const bar = document.querySelector(".bottom-nav");
if (bar) {
  const bubble = bar.querySelector(".bn-bubble");
  const items = [...bar.querySelectorAll(".bn-item")];

  const moveTo = (item, animate = true) => {
    if (!bubble || !item) return;
    if (!animate) bubble.style.transition = "none";
    const barBox = bar.getBoundingClientRect();
    const box = item.getBoundingClientRect();
    const radius = bubble.offsetWidth / 2;
    // getBoundingClientRect is always physical/viewport space, so this
    // needs no RTL branch: the bubble's untransformed rest position is
    // pinned to the bar's physical left edge (`left:0`), and translating
    // it by (item's physical center − bar's physical left − radius)
    // lands it centered under the item regardless of text direction.
    const offset = box.left + box.width / 2 - barBox.left - radius;
    bubble.style.transform = `translateX(${offset}px)`;
    if (!animate) {
      void bubble.offsetWidth; // flush, then restore the transition
      bubble.style.transition = "";
    }
  };

  const setActive = (item) => {
    items.forEach((other) => {
      const on = other === item;
      other.classList.toggle("is-active", on);
      if (on) other.setAttribute("aria-current", "page");
      else other.removeAttribute("aria-current");
    });
    moveTo(item);
  };

  const initial = items.find((item) => item.classList.contains("is-active")) || items[0];
  // The bar is display:none above 980px, so a zero-width measurement
  // means we are on desktop — wait for a resize into mobile instead.
  const place = () => {
    if (bar.getBoundingClientRect().width > 0) moveTo(initial, false);
  };
  place();
  requestAnimationFrame(place);
  addEventListener("resize", () => {
    const current = items.find((item) => item.classList.contains("is-active")) || initial;
    moveTo(current, false);
  });

  items.forEach((item) =>
    item.addEventListener("click", () => {
      // Move immediately on tap; the navigation that follows re-renders
      // the bar anyway, but the bubble should not wait for it.
      setActive(item);
    }),
  );
}
