/* site-header — mobile panel toggle with body scroll lock and Escape to close. */
document.querySelectorAll('[data-block="site-header"]').forEach((header) => {
  const button = header.querySelector('.menu-button');
  const panel = document.querySelector('.mobile-panel');
  if (!button || !panel) return;

  const setOpen = (open) => {
    panel.classList.toggle('open', open);
    button.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('menu-open', open);
  };

  button.addEventListener('click', () => setOpen(!panel.classList.contains('open')));
  panel.addEventListener('click', (event) => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && panel.classList.contains('open')) {
      setOpen(false);
      button.focus();
    }
  });
});
