# Source photographs

The original JPEGs from the Didanshow installation archive. They are the
masters and they stay here: the owner's standing rule is that an earlier
version of a piece of work is never deleted or replaced, only kept alongside
the new one.

What ships is the `.webp` beside them, at quality 82. The built page inlines
whatever it references, so a 1.5 MB set of JPEGs became 1.5 MB of base64 in
every visitor's first request.

This folder is deliberately a subfolder: the composer copies only the files a
page actually references from the media directory, and nothing references
these.

Regenerate after replacing a master:

```python
from PIL import Image
Image.open("source/installation-01.jpg").save(
    "installation-01.webp", "WEBP", quality=82, method=6)
```
