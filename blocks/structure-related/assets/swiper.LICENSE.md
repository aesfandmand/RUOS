swiper.min.mjs / swiper-base.css — vendored build provenance
================================================================

Source: `swiper` 14.1.0 (npm), MIT License, Copyright (c) 2019 Vladimir
Kharlampidi. https://swiperjs.com

Built with esbuild from the core module plus only the Navigation, A11y
and Keyboard modules (no Autoplay: motion should be user-driven, not
automatic, and this respects prefers-reduced-motion the same way the
rest of the engine does):

    import Swiper from "swiper";
    import { Navigation, A11y, Keyboard } from "swiper/modules";
    Swiper.use([Navigation, A11y, Keyboard]);
    export { Swiper };

    npx esbuild entry.mjs --bundle --format=esm --minify \
      --outfile=swiper.min.mjs --target=es2020

`swiper-base.css` is the package's own unmodified `swiper.min.css`
(core slide/wrapper layout only — no theme skinning, which this block's
own style.css supplies).

MIT License text:

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
