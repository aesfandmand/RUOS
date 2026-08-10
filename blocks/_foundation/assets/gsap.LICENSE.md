gsap.min.mjs — vendored build provenance
=========================================

Source package (npm): `gsap` 3.15.0 — https://www.npmjs.com/package/gsap
Copyright (c) 2008-2026, GreenSock (owned by Webflow).

Built with `esbuild` from the package's real ESM entry points, bundling
the animation core plus two plugins — ScrollTrigger and SplitText. No
other GSAP plugin (Draggable, MorphSVG, Flip, Observer, ...) is
included. Zero unresolved imports in the output.

Build command:

    npx esbuild entry.js --bundle --format=esm --minify \
      --outfile=gsap.min.mjs --target=es2020

where entry.js was:

    export { gsap } from "gsap";
    export { ScrollTrigger } from "gsap/ScrollTrigger";
    export { SplitText } from "gsap/SplitText";

License: GreenSock's Standard "no charge" license
(https://gsap.com/standard-license) — **not MIT**. Since GSAP 3.13
(2024), GSAP's core and every plugin — including ScrollTrigger and the
plugins formerly restricted to paying "Club GreenSock" members, of which
SplitText is one — are free for commercial use on client/agency projects
like this one, sponsored by Webflow. Confirmed via the package's own
`package.json` (`"license": "Standard 'no charge' license: ..."`), the
presence of `SplitText.js` inside the free npm package itself, and
GreenSock's public licensing page — not assumed from memory.

SplitText is vendored specifically for per-character/per-word heading
animation, which the owner approved as part of the design model.
