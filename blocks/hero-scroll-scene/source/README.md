# Source artwork for this block

`hero-city.png` is the original 1536×1024 render (2743 KB). It is the master
and it stays here: the owner's standing rule is that an earlier version of a
piece of work is never deleted or replaced, only kept alongside the new one.

What ships is `../assets/hero-city.webp` — the same image at WebP quality 82,
240 KB, a 91% saving. Measured against the master, the mean per-channel
difference is about 3/255 (~1.2%), and the hero applies
`saturate(.82) brightness(.76) contrast(1.05)` over the top, which absorbs
more of that than it adds.

This folder is deliberately **not** `assets/`: the composer copies every file
in a block's `assets/` directory into the built page, so a master kept there
would be shipped to every visitor even though nothing references it.

To regenerate the shipped file after editing the master:

```python
from PIL import Image
Image.open("source/hero-city.png").save(
    "assets/hero-city.webp", "WEBP", quality=82, method=6)
```
