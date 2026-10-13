import { Swiper, Navigation, Pagination, EffectCoverflow, A11y, Keyboard } from "./swiper-coverflow.min.mjs";

document.querySelectorAll(".service-cf-swiper").forEach((el) => {
  const stage = el.closest(".service-cf-stage");
  if (!stage) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  new Swiper(el, {
    modules: [Navigation, Pagination, EffectCoverflow, A11y, Keyboard],
    // Rotation is kept. Dropping rotateY to work around Safari's flattening
    // was the wrong fix (motion-verbs-v1.yaml → perspective-drag); the layer
    // isolation in style.css is the right one.
    effect: reduced ? "slide" : "coverflow",
    grabCursor: true,
    centeredSlides: true,
    slidesPerView: "auto",
    dir: "rtl",
    coverflowEffect: {
      rotate: 38,
      stretch: -24,
      depth: 300,
      scale: 0.92,
      modifier: 1,
      slideShadows: false,
    },
    a11y: {
      enabled: true,
      prevSlideMessage: "راهکار قبلی",
      nextSlideMessage: "راهکار بعدی",
      firstSlideMessage: "این اولین راهکار است",
      lastSlideMessage: "این آخرین راهکار است",
      slideLabelMessage: "راهکار {{index}} از {{slidesLength}}",
      containerMessage: "راهکارها بر اساس نوع سفارش‌دهنده",
    },
    keyboard: { enabled: true },
    pagination: { el: stage.querySelector(".service-cf-pagination"), type: "fraction" },
    watchSlidesProgress: true,
    navigation: {
      nextEl: stage.querySelector(".service-cf-next"),
      prevEl: stage.querySelector(".service-cf-prev"),
    },
  });
});
