// Named import, not "Swiper": structure-gallery also imports a top-level
// "Swiper" binding (from its own coverflow bundle), and block_composer
// concatenates every block's behavior.js into one shared module scope --
// two same-named top-level imports there is a SyntaxError that silently
// kills ALL page JS, on any page composing both blocks together.
import { Swiper as SwiperRelated } from "./swiper.min.mjs";

document.querySelectorAll(".structure-related-swiper").forEach((el) => {
  const root = el.closest(".structure-related");
  new SwiperRelated(el, {
    slidesPerView: 1.15,
    spaceBetween: 16,
    dir: "rtl",
    a11y: {
      enabled: true,
      prevSlideMessage: "مورد قبلی",
      nextSlideMessage: "مورد بعدی",
      firstSlideMessage: "این اولین مورد است",
      lastSlideMessage: "این آخرین مورد است",
      paginationBulletMessage: "برو به مورد {{index}}",
      slideLabelMessage: "مورد {{index}} از {{slidesLength}}",
      containerMessage: "سازه‌های مرتبط",
    },
    keyboard: { enabled: true },
    navigation: {
      nextEl: root.querySelector(".structure-related-next"),
      prevEl: root.querySelector(".structure-related-prev"),
    },
    breakpoints: {
      640: { slidesPerView: 2.2, spaceBetween: 20 },
      980: { slidesPerView: 3.3, spaceBetween: 24 },
    },
  });
});
