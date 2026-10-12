# Drafts — not yet approved

A page spec lives here until the owner has approved it on **both** breakpoints.
Design model §5: approval is a conversation, never a script flag, and only an
approved page's JSON is written to `pages/blocks/<slug>.json` — that move is
also what takes it out of the build queue.

Build one with:

```
python3 tools/build_services_hub.py pages/drafts/services.json
python3 -m ruos.cli compose  services --spec-root pages/drafts
python3 -m ruos.cli critique services --spec-root pages/drafts
```

## services.json

The `/services/` hub. Structure and every number come from the architecture
registry v2.1; the six families, their order, their service counts and their
subgroup counts are all counted at build time, never typed in. Anything that
would be a marketing claim nobody has written yet ships as tagged Lorem Ipsum
(`"placeholder": true`) per design model §2 — the page ships complete, and it
never passes off an invented sentence as real copy.

Waiting on the human copy pass: the family descriptions, the process steps,
the "choosing between families" comparisons, the FAQ answers, and ten image
slots (no service photography exists yet).
