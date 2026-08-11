// Mobile bottom nav: drive the liquid bubble to whichever item is active.
// The only thing this file sets is --bn-x (the bubble's centre, measured
// rather than hard-coded so the bar works with any number of entries); the
// stylesheet derives the notch in the bar, the bubble and the raised icon
// from it. `.is-moving` runs the dip-and-tumble for the length of a trip.

const bar = document.querySelector(".bottom-nav");
if (bar) {
  const items = [...bar.querySelectorAll(".bn-item")];
  let settle = 0;

  const moveTo = (item, animate = true) => {
    if (!item) return;
    if (!animate) bar.style.transition = "none";
    const barBox = bar.getBoundingClientRect();
    const box = item.getBoundingClientRect();
    // getBoundingClientRect is physical/viewport space, so this needs no
    // RTL branch: the offset from the bar's physical left edge to the
    // item's physical centre is correct in either direction.
    bar.style.setProperty("--bn-x", `${box.left + box.width / 2 - barBox.left}px`);
    if (!animate) {
      void bar.offsetWidth; // flush, then restore the transition
      bar.style.transition = "";
      return;
    }
    // restart the dip even if a trip is already in flight
    bar.classList.remove("is-moving");
    void bar.offsetWidth;
    bar.classList.add("is-moving");
    clearTimeout(settle);
    settle = setTimeout(() => bar.classList.remove("is-moving"), 560);
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
