// Site header: mega-menu (desktop) and the drawer (mobile).
// The visible motion lives in style.css transitions; this file only owns
// state, so a reduced-motion visitor gets the same behaviour with the
// transitions collapsed by the stylesheet.

const header = document.querySelector(".site-header");
if (header) {
  const megaItems = [...header.querySelectorAll(".mega-item")];

  const closeMega = (item) => {
    item.classList.remove("is-open");
    item.querySelector(".mega-trigger")?.setAttribute("aria-expanded", "false");
  };
  const closeAllMega = () => megaItems.forEach(closeMega);

  // A mouse gets hover-to-open; a touch screen gets tap-to-toggle. Binding
  // both on a hover-capable device makes them fight — the pointer opens the
  // panel and the click that follows immediately toggles it shut again.
  const canHover = matchMedia("(hover: hover) and (pointer: fine)").matches;

  const openMega = (item) => {
    closeAllMega();
    item.classList.add("is-open");
    item.querySelector(".mega-trigger")?.setAttribute("aria-expanded", "true");
  };

  megaItems.forEach((item) => {
    if (canHover) {
      item.addEventListener("pointerenter", () => openMega(item));
      item.addEventListener("pointerleave", () => closeMega(item));
      // Keyboard users never fire pointer events, so they still need this.
      item.querySelector(".mega-trigger")?.addEventListener("focus", () => openMega(item));
    } else {
      item.querySelector(".mega-trigger")?.addEventListener("click", () => {
        if (item.classList.contains("is-open")) closeMega(item);
        else openMega(item);
      });
    }
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".mega-item")) closeAllMega();
  });

  const menuButton = header.querySelector(".menu-button");
  const drawer = document.querySelector(".mobile-menu");

  const setDrawer = (open) => {
    if (!drawer || !menuButton) return;
    menuButton.setAttribute("aria-expanded", String(open));
    menuButton.setAttribute("aria-label", open ? "بستن منو" : "باز کردن منو");
    document.body.classList.toggle("no-scroll", open);
    if (open) {
      drawer.hidden = false;
      // one frame between unhiding and adding the class, so the browser
      // has a "from" state to transition out of
      requestAnimationFrame(() => drawer.classList.add("is-open"));
    } else {
      drawer.classList.remove("is-open");
      const done = () => { drawer.hidden = true; };
      drawer.addEventListener("transitionend", done, { once: true });
      setTimeout(done, 400);
    }
  };

  menuButton?.addEventListener("click", () => {
    setDrawer(menuButton.getAttribute("aria-expanded") !== "true");
  });
  drawer?.querySelectorAll("a").forEach((link) =>
    link.addEventListener("click", () => setDrawer(false)),
  );

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    closeAllMega();
    if (menuButton?.getAttribute("aria-expanded") === "true") {
      setDrawer(false);
      menuButton.focus();
    }
  });
}
