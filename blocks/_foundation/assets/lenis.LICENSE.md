lenis.min.mjs — vendored build provenance
==========================================

Source package (npm): `lenis` 1.3.26 — https://www.npmjs.com/package/lenis
MIT licensed — Studio Freight / darkroom.engineering.

Smooth-scroll engine. Chosen (and approved by the owner) to give the
page the gliding scroll feel of the Awwwards-style references the owner
supplied; the browser's native scroll cannot produce it. It also gives
GSAP ScrollTrigger a single, consistent scroll source to sync against,
instead of the two fighting each other.

Built with `esbuild` from the package's real ESM entry point:

    npx esbuild entry.js --bundle --format=esm --minify \
      --outfile=lenis.min.mjs --target=es2020

where entry.js was:

    export { default as Lenis } from "lenis";

Zero unresolved imports in the output. The package's optional
`dist/lenis.css` is NOT vendored — its only rules concern `data-lenis-*`
attributes we do not use; the two properties actually needed are set
directly in _foundation/style.css so there is no extra stylesheet to
keep in sync.

Every use must stay behind `prefers-reduced-motion: reduce` — a visitor
who asked the OS for less motion gets native scrolling.
