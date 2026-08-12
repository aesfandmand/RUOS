import { scroll } from "./motion.min.mjs";

(() => {
  const clamp = (value) => Math.min(1, Math.max(0, value));
  const fa = (value) => new Intl.NumberFormat("fa-IR", { useGrouping: false }).format(value);
  const hero = document.querySelector(".hero-scroll");
  const opportunity = document.querySelector(".opportunity-section");
  const paths = document.querySelector(".paths-scroll");
  const status = document.querySelector(".story-status > span:last-child");
  let frame = 0;

  // The hero's scroll progress (0 at its top reaching the viewport top, 1 at
  // its bottom reaching the viewport bottom) drives --hero-progress, which
  // the rest of update() below reads. Motion's scroll() replaces the manual
  // getBoundingClientRect() math this used to do on every rAF tick with a
  // single scroll-linked subscription.
  let heroProgress = 0;
  if (hero) {
    scroll((progress) => {
      heroProgress = clamp(progress);
      hero.style.setProperty("--hero-progress", String(heroProgress));
    }, { target: hero, offset: ["start start", "end end"] });
  }

  const setPath = (index) => {
    document.querySelectorAll(".path-card").forEach((card, cardIndex) => {
      card.classList.toggle("is-current", cardIndex === index);
      card.classList.toggle("is-past", cardIndex < index);
      card.classList.toggle("is-future", cardIndex > index);
      card.setAttribute("aria-hidden", cardIndex === index ? "false" : "true");
    });
    document.querySelectorAll(".path-stepper button").forEach((button, buttonIndex) => {
      button.classList.toggle("is-active", buttonIndex === index);
    });
    const hint = document.querySelector(".path-mobile-hint");
    if (hint) hint.lastChild.textContent = " کارت " + fa(index + 1) + " از ۳";
  };

  const update = () => {
    frame = 0;
    const viewport = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight - viewport;
    document.documentElement.style.setProperty("--reading-progress", String(documentHeight > 0 ? window.scrollY / documentHeight : 0));
    if (!hero || !opportunity || !paths) return;

    const heroRect = hero.getBoundingClientRect();
    const starts = [0.08, 0.34, 0.62];
    let bornCount = 0;
    hero.querySelectorAll(".birth-structure").forEach((board, index) => {
      const born = clamp((heroProgress - starts[index]) / 0.22);
      board.style.setProperty("--born", String(born));
      board.style.setProperty("--rise", String((1 - born) * 170) + "px");
      board.style.setProperty("--board-scale", String(0.55 + born * 0.45));
      board.style.setProperty("--board-opacity", String(Math.min(1, born * 1.5)));
      board.style.setProperty("--fill-x", String((1 - born) * 100) + "%");
      if (heroProgress > starts[index] + 0.13) bornCount += 1;
    });
    hero.style.setProperty("--drive-x", String(-18 + clamp((heroProgress - 0.14) / 0.74) * 93) + "%");
    hero.querySelectorAll(".birth-meter span").forEach((item, index) => item.classList.toggle("is-born", index < bornCount));

    const opportunityRect = opportunity.getBoundingClientRect();
    let activeOpportunity = 0;
    let nearest = Infinity;
    opportunity.querySelectorAll("[data-opportunity]").forEach((story, index) => {
      const rect = story.getBoundingClientRect();
      const distance = Math.abs(rect.top + rect.height / 2 - viewport * 0.5);
      if (distance < nearest) { nearest = distance; activeOpportunity = index; }
    });
    opportunity.querySelectorAll("[data-opportunity]").forEach((story, index) => story.classList.toggle("is-active", index === activeOpportunity));

    const pathsRect = paths.getBoundingClientRect();
    const pathsProgress = clamp(-pathsRect.top / Math.max(1, pathsRect.height - viewport));
    const pathIndex = pathsProgress < 0.335 ? 0 : pathsProgress < 0.67 ? 1 : 2;
    setPath(pathIndex);

    if (status) {
      status.textContent = heroRect.bottom > viewport * 0.22
        ? "شهر زنده · " + fa(bornCount) + " از ۳ سازه متولد شد"
        : opportunityRect.bottom > viewport * 0.28
          ? "فرصت دیده‌نشده · موقعیت " + fa(activeOpportunity + 1) + " از ۴"
          : pathsRect.bottom > viewport * 0.3
            ? "سه مسیر · مسیر " + fa(pathIndex + 1) + " از ۳"
            : "پروندهٔ تصمیم · سازه، قرارداد و امکان‌سنجی";
    }
  };

  const requestUpdate = () => { if (!frame) frame = requestAnimationFrame(update); };
  addEventListener("scroll", requestUpdate, { passive: true });
  addEventListener("resize", requestUpdate);
  update();

  // Scroll reveal. Every [data-reveal] eases in once as it enters; anything
  // inside a [data-reveal-group] gets an incrementing --reveal-i so a row of
  // cards arrives one behind another instead of all at once.
  //
  // This must FAIL OPEN. A hidden element that never gets its class is
  // invisible content, not a missing animation, so alongside the observer
  // there is a sweep that reveals anything the viewport has already reached.
  // A fast flick outruns IntersectionObserver's delivery and would otherwise
  // leave whole sections blank.
  const pending = new Set(document.querySelectorAll("[data-reveal]"));
  document.querySelectorAll("[data-reveal-group]").forEach((group) => {
    group.querySelectorAll("[data-reveal]").forEach((child, index) => {
      child.style.setProperty("--reveal-i", String(index));
    });
  });
  const reveal = (element) => {
    element.classList.add("is-in");
    pending.delete(element);
    revealer.unobserve(element);
  };
  const revealer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => { if (entry.isIntersecting) reveal(entry.target); });
  }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
  pending.forEach((element) => revealer.observe(element));

  let sweeping = 0;
  const sweep = () => {
    sweeping = 0;
    pending.forEach((element) => {
      // anything whose top edge the viewport has already passed is overdue
      if (element.getBoundingClientRect().top < innerHeight) reveal(element);
    });
  };
  addEventListener("scroll", () => { if (!sweeping) sweeping = requestAnimationFrame(sweep); }, { passive: true });
  addEventListener("resize", sweep);

  // Depth on scroll: the hero image drifts a little slower than the page.
  const heroShot = document.querySelector(".p-hero-stage");
  if (heroShot) {
    let ticking = 0;
    const drift = () => {
      ticking = 0;
      const offset = Math.min(window.scrollY, 420);
      heroShot.style.setProperty("--drift", `${offset * 0.12}px`);
      heroShot.style.setProperty("--zoom", String(1 + Math.min(offset, 300) * 0.00016));
    };
    addEventListener("scroll", () => { if (!ticking) ticking = requestAnimationFrame(drift); }, { passive: true });
    drift();
  }

  // The mobile drawer is owned by blocks/site-header/behavior.js — it has
  // to manage the `hidden` attribute and the open/close transition together,
  // which a second handler here would fight over.

  document.querySelectorAll(".path-stepper button").forEach((button, index) => button.addEventListener("click", () => {
    const top = scrollY + paths.getBoundingClientRect().top;
    const distance = paths.offsetHeight - innerHeight;
    scrollTo({ top: top + distance * (index / 2), behavior: "smooth" });
  }));

  const filterButtons = [...document.querySelectorAll(".product-toolbar button")];
  const productCards = [...document.querySelectorAll(".products-grid .product-card")];
  filterButtons.forEach((button, filterIndex) => button.addEventListener("click", () => {
    filterButtons.forEach((item, index) => {
      item.classList.toggle("is-active", index === filterIndex);
      item.setAttribute("aria-pressed", String(index === filterIndex));
    });
    productCards.forEach((card, cardIndex) => {
      const visible = filterIndex === 0 || (filterIndex === 1 && cardIndex < 11) || (filterIndex === 2 && cardIndex >= 11);
      card.hidden = !visible;
    });
  }));

  const questionScores = [[3,3,3,0],[3,2,2,0],[3,2,0,1]];
  const answers = [null, null, null];
  const fieldsets = [...document.querySelectorAll(".assessment-questions fieldset")];
  const progress = document.querySelector(".assessment-progress i");
  const result = document.querySelector(".assessment-result");
  const resultLabel = result?.querySelector(":scope > small");
  const resultTitle = result?.querySelector("h3");
  const resultText = result?.querySelector(":scope > p");
  const refreshAssessment = () => {
    const count = answers.filter((answer) => answer !== null).length;
    const score = answers.reduce((total, answer, index) => total + (answer === null ? 0 : questionScores[index][answer]), 0);
    if (progress) progress.style.width = String(count / 3 * 100) + "%";
    if (!result || !resultLabel || !resultTitle || !resultText) return;
    result.classList.toggle("is-ready", count === 3);
    if (count < 3) {
      resultLabel.textContent = fa(count) + " از ۳ پاسخ ثبت شده";
      resultTitle.textContent = "سه نشانه را کامل کنید تا قدم بعد روشن شود.";
      resultText.textContent = "این ارزیابی عدد درآمد تولید نمی‌کند؛ فقط اولویت بازدید و مانع اصلی را مشخص می‌کند.";
    } else if (score >= 8) {
      resultLabel.textContent = "اولویت بالا برای امکان‌سنجی";
      resultTitle.textContent = "موقعیت شما ارزش یک بررسی میدانی جدی دارد.";
      resultText.textContent = "قدم بعد، ثبت موقعیت و بررسی حق فضا، زاویه دید، زیرساخت و بازار منطقه است؛ نه انتخاب فوری سازه.";
    } else if (score >= 5) {
      resultLabel.textContent = "قابل بررسی با یک مانع روشن";
      resultTitle.textContent = "ظرفیت وجود دارد، اما یک ابهام باید زودتر حل شود.";
      resultText.textContent = "بازدید اولیه کمک می‌کند مشخص شود مانع اصلی از جنس حق فضا، جانمایی یا زیرساخت است.";
    } else {
      resultLabel.textContent = "ابتدا مانع اصلی را روشن کنیم";
      resultTitle.textContent = "هنوز برای ورود به ساخت زود است.";
      resultText.textContent = "این نتیجه رد موقعیت نیست؛ فقط ترتیب درست را نشان می‌دهد: اول حق فضا و کیفیت دید، بعد مدل مالی و سازه.";
    }
  };
  fieldsets.forEach((fieldset, questionIndex) => {
    const buttons = [...fieldset.querySelectorAll(".assessment-options button")];
    buttons.forEach((button, optionIndex) => button.addEventListener("click", () => {
      answers[questionIndex] = optionIndex;
      buttons.forEach((item, index) => {
        item.classList.toggle("is-selected", index === optionIndex);
        item.setAttribute("aria-pressed", String(index === optionIndex));
      });
      refreshAssessment();
    }));
  });

  document.querySelectorAll("button.contact-link, .hero-actions button, .review-actions button, .footer-contact button, .assessment-result .primary-button").forEach((button) => {
    button.addEventListener("click", () => document.querySelector("#review")?.scrollIntoView({ behavior: "smooth" }));
  });
})();
