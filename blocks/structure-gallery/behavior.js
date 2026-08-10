import { Swiper, Navigation, Pagination, EffectCoverflow, A11y, Keyboard } from "./swiper-coverflow.min.mjs";

document.querySelectorAll(".structure-gallery-swiper").forEach((el) => {
  const root = el.closest(".structure-gallery-stage");
  new Swiper(el, {
    modules: [Navigation, Pagination, EffectCoverflow, A11y, Keyboard],
    effect: "coverflow",
    grabCursor: true,
    centeredSlides: true,
    slidesPerView: "auto",
    dir: "rtl",
    coverflowEffect: {
      rotate: 34,
      stretch: 0,
      depth: 180,
      modifier: 1,
      slideShadows: false,
    },
    a11y: {
      enabled: true,
      prevSlideMessage: "مورد قبلی",
      nextSlideMessage: "مورد بعدی",
      firstSlideMessage: "این اولین مورد است",
      lastSlideMessage: "این آخرین مورد است",
      slideLabelMessage: "مورد {{index}} از {{slidesLength}}",
      containerMessage: "گالری نصب واقعی",
    },
    keyboard: { enabled: true },
    pagination: {
      el: root.querySelector(".structure-gallery-pagination"),
      type: "fraction",
    },
    navigation: {
      nextEl: root.querySelector(".structure-gallery-next"),
      prevEl: root.querySelector(".structure-gallery-prev"),
    },
  });
});
