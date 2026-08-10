gsap.min.mjs — vendored build provenance
=========================================

Source package (npm): `gsap` 3.15.0 — https://www.npmjs.com/package/gsap
Copyright (c) 2008-2026, GreenSock (owned by Webflow).

Built with `esbuild` from the package's real ESM entry points, bundling
only the animation core and the ScrollTrigger plugin — no other GSAP
plugin (Draggable, MorphSVG, Flip, etc.) is included. Zero unresolved
imports in the output.

Build command:

    npx esbuild entry.js --bundle --format=esm --minify \
      --outfile=gsap.min.mjs --target=es2020

where entry.js was:

    export { gsap } from "gsap";
    export { ScrollTrigger } from "gsap/ScrollTrigger";

License: GreenSock's Standard "no charge" license
(https://gsap.com/standard-license) — **not MIT**. Since GSAP 3.13
(2024), GSAP's core and every plugin, including ScrollTrigger and the
plugins formerly restricted to paying "Club GreenSock" members
(SplitText, MorphSVG, etc. — none of which are vendored here), are free
for commercial use on client/agency projects like this one, sponsored by
Webflow. Confirmed via the package's own `package.json` (`"license":
"Standard 'no charge' license: https://gsap.com/standard-license"`) and
GreenSock's public licensing page, not assumed from memory.
