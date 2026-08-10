// Mobile bottom nav: position the sliding "liquid" pill under whichever
// item is active. Geometry is measured rather than hard-coded so the bar
// works with any number of entries and any label width.

const bar = document.querySelector(".bottom-nav");
if (bar) {
  const bubble = bar.querySelector(".bn-bubble");
  const items = [...bar.querySelectorAll(".bn-item")];

  const moveTo = (item, animate = true) => {
    if (!bubble || !item) return;
    if (!animate) bubble.style.transition = "none";
    const barBox = bar.getBoundingClientRect();
    const box = item.getBoundingClientRect();
    // RTL-safe: translate from the bar's inline-start edge, whichever
    // physical side that is.
    const rtl = getComputedStyle(bar).direction === "rtl";
    const offset = rtl ? barBox.right - box.right : box.left - barBox.left;
    bubble.style.width = `${box.width}px`;
    bubble.style.transform = `translateX(${rtl ? -offset : offset}px)`;
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
      // the bar anyway, but the pill should not wait for it.
      setActive(item);
    }),
  );
}
