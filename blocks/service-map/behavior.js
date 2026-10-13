// service-map filters. Progressive: every card is visible in the markup and
// stays visible if this never runs. The filter only ever hides cards the
// visitor asked to hide, and "همه" restores all of them.
(() => {
  document.querySelectorAll('[data-block="service-map"]').forEach((section) => {
    const buttons = [...section.querySelectorAll(".service-filter")];
    const cards = [...section.querySelectorAll(".service-card")];
    if (!buttons.length || !cards.length) return;

    const apply = (value) => {
      cards.forEach((card) => {
        const groups = (card.dataset.groups || "").split(/\s+/).filter(Boolean);
        card.hidden = value !== "all" && !groups.includes(value);
      });
      buttons.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.filter === value));
      });
    };

    buttons.forEach((button) => {
      button.addEventListener("click", () => apply(button.dataset.filter || "all"));
    });

    apply(buttons[0].dataset.filter || "all");
  });
})();
