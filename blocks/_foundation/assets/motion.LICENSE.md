motion.min.mjs — vendored build provenance
===========================================

Source packages (npm, MIT-licensed):

- `framer-motion` 13.0.0 — https://www.npmjs.com/package/framer-motion
- `motion-dom` 13.0.0 — https://www.npmjs.com/package/motion-dom
- `motion-utils` 13.0.0 — https://www.npmjs.com/package/motion-utils

Built with `esbuild` from the DOM-only, React-free entry point
(`framer-motion/dom`), bundling only `animate`, `scroll`, `inView` and
`stagger` and tree-shaking everything else (React components, gesture
recognisers, layout-projection code). No React dependency is present in
the output; it is a plain ES module with zero unresolved imports.

Build command:

    npx esbuild entry.mjs --bundle --format=esm --minify \
      --outfile=motion.min.mjs --target=es2020

where entry.mjs was:

    export { animate, scroll, inView, stagger } from "framer-motion/dom";

sha256: 39a303021d4a20902d4d87dd1f11f1e1f57d3972cfae88b638435898d4c899c4

License (MIT, Framer B.V.):

The MIT License (MIT)

Copyright (c) 2018 Framer B.V.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
