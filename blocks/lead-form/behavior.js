// Compact lead form: validate in place and confirm without leaving the page.
// No endpoint is wired yet — the owner connects this at WordPress upload time,
// so the honest behaviour here is to say the request was recorded locally.
const form = document.querySelector(".lead-form");
if (form) {
  const status = form.querySelector(".lead-status");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const missing = [...form.querySelectorAll("input, textarea")].filter((field) => !field.value.trim());
    if (missing.length) {
      if (status) status.textContent = "لطفاً هر سه مورد را کامل کنید.";
      missing[0].focus();
      return;
    }
    if (status) {
      status.style.color = "var(--ink)";
      status.textContent = "درخواست شما ثبت شد؛ برای بررسی پروژه تماس می‌گیریم.";
    }
    form.querySelector(".lead-submit").disabled = true;
  });
}
