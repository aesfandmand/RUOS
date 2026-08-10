icon-sprite.svg — vendored build provenance
=============================================

Source: `@phosphor-icons/core` 2.1.1 (npm), "regular" weight SVGs.
MIT licensed — Phosphor Icons (https://phosphoricons.com), copyright the
Phosphor Icons project.

Chosen after the owner compared real renders of Lucide, Tabler and
Phosphor side by side (same 10 icons, same size) and approved this
family — see the icon-compare artifact from that review. Phosphor's six
consistent weights (thin/light/regular/bold/fill/duotone) of the same
glyph give room for real active/inactive icon states later (e.g. the
bottom-nav, mega-menu) without switching icon families.

10 icons extracted as an inline `<symbol>` sprite (path data only,
`fill="currentColor"` so each use inherits the surrounding text color).
Symbol IDs are unchanged from the previous Font Awesome sprite so no
block markup needed to change — only the underlying artwork:

- icon-ruler → ruler
- icon-location → map-pin
- icon-shield → shield
- icon-faq → question
- icon-related → link-simple
- icon-services → wrench
- icon-chevron-left → caret-left
- icon-chevron-right → caret-right
- icon-external → arrow-square-out
- icon-datasheet → file-text

No other part of the Phosphor package (React/Vue components, other
weights, build tooling) is included — only these ten regular-weight path
definitions.
