import { Swiper } from "./swiper.min.mjs";

document.querySelectorAll(".structure-related-swiper").forEach((el) => {
  const root = el.closest(".structure-related");
  new Swiper(el, {
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
