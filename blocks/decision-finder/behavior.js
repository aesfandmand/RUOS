/* decision-finder — scoped to each instance so a page may host more than one. */
document.querySelectorAll('[data-block="decision-finder"]').forEach((root) => {
  const payload = root.querySelector('script[data-finder-outcomes]');
  if (!payload) return;
  const outcomes = JSON.parse(payload.textContent);
  const fallback = root.dataset.finderFallback;
  const groups = [...root.querySelectorAll('.sp-choice')];
  const title = root.querySelector('[data-finder-title]');
  const body = root.querySelector('[data-finder-body]');
  const list = root.querySelector('[data-finder-points]');
  const state = {};

  groups.forEach((group) => {
    const pressed = group.querySelector('button[aria-pressed="true"]') || group.querySelector('button');
    state[group.dataset.group] = pressed ? pressed.dataset.value : '';
  });

  const key = () => groups.map((group) => state[group.dataset.group]).join('|');

  const render = () => {
    const match = outcomes[key()] || outcomes[fallback];
    if (!match) return;
    title.textContent = match.title;
    body.textContent = match.body;
    list.replaceChildren(...match.points.map((point) => {
      const li = document.createElement('li');
      li.textContent = point;
      return li;
    }));
  };

  groups.forEach((group) => {
    group.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', () => {
        group.querySelectorAll('button').forEach((other) => {
          other.setAttribute('aria-pressed', String(other === button));
        });
        state[group.dataset.group] = button.dataset.value;
        render();
      });
    });
  });
});
