"""Build an owner-review preview of a structure's complete-draft page --
both breakpoints screenshotted -- before anything is committed.

    python3 tools/build_draft_preview.py <structure-id> [output-dir]

Never writes to pages/blocks/ or dist/: the whole point of this tool is
that the result is a draft, gated on the owner's explicit approval in
chat before it becomes a real, committed page (see design model §20).
Screenshots both mobile (390x844, matching the iPhone 13 viewport this
project already verifies against per CLAUDE.md §7) and desktop
(1440x900) so both are reviewed, per the owner's explicit requirement,
before a page is ever considered done.
"""
from __future__ import annotations

import http.server
import re
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ruos.architecture_registry import load_structures  # noqa: E402
from ruos.block_page import render_page  # noqa: E402
from ruos.block_registry import load_library  # noqa: E402
from ruos.cli import _write_composed_page  # noqa: E402
from ruos.structure_detail_spec import build_complete_draft_spec  # noqa: E402


def _find_structure(structure_id: str):
    structure = next(
        (s for s in load_structures()
         if s.id == structure_id or s.url.strip("/").rsplit("/", 1)[-1] == structure_id),
        None,
    )
    if structure is None:
        raise SystemExit(f"No structure matches '{structure_id}'")
    return structure


def build_preview(structure_id: str, output_dir: Path) -> Path:
    structure = _find_structure(structure_id)
    library = load_library()
    spec = build_complete_draft_spec(structure)
    page = render_page(spec, library)
    _write_composed_page(page, library, output_dir)
    return output_dir


def build_standalone_html(structure_id: str, out_path: Path) -> Path:
    """One self-contained .html file -- CSS, script, vendor imports and the
    header logo all inlined -- so it opens directly in a real browser over
    file:// and the owner can resize it, scroll it and actually interact
    with it. Per the owner's explicit instruction (2026-08-13): approval
    needs the real page, not a screenshot of it."""
    import base64

    structure = _find_structure(structure_id)
    library = load_library()
    spec = build_complete_draft_spec(structure)
    page = render_page(spec, library)

    html = page.html.replace(
        '<link rel="stylesheet" href="assets/styles.css">', f"<style>{page.css}</style>",
    )

    script = page.script
    for match in re.findall(r'from\s+["\'](\./[^"\']+\.mjs)["\']', script):
        name = match.split("/")[-1]
        vendor_path = next(ROOT.glob(f"blocks/*/assets/{name}"), None)
        if vendor_path is None:
            raise SystemExit(f"Vendor asset referenced in behavior.js not found: {name}")
        vendor_uri = "data:text/javascript;base64," + base64.b64encode(vendor_path.read_bytes()).decode("ascii")
        script = script.replace(f'"{match}"', f'"{vendor_uri}"')
    html = html.replace(
        '<script type="module" src="assets/behavior.js"></script>', f'<script type="module">{script}</script>',
    )
    html = html.replace(
        '<script src="assets/behavior.js" defer></script>', f'<script type="module">{script}</script>',
    )

    logo_path = ROOT / "blocks" / "site-header" / "assets" / "logo.png"
    logo_uri = "data:image/png;base64," + base64.b64encode(logo_path.read_bytes()).decode("ascii")
    html = html.replace('src="assets/logo.png"', f'src="{logo_uri}"')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def _reveal_everything(page) -> None:
    """A full_page screenshot captures the whole scrollable area in one CDP
    call (Page.captureScreenshot with captureBeyondViewport) rather than
    actually scrolling the real viewport through the page, so the
    [data-reveal] IntersectionObserver never observes most of the page and
    everything below the fold is captured mid-fade at opacity:0 -- a real
    visitor scrolling the real viewport does not hit this, only this
    screenshot method does. Force every reveal into the same "is-in" state
    the observer itself applies (see blocks/_foundation/behavior.js) so the
    static capture shows the settled, revealed page a real visit ends up
    seeing."""
    page.evaluate(
        "document.querySelectorAll('[data-reveal],[data-reveal-group] > *')"
        ".forEach((el) => el.classList.add('is-in'))"
    )
    page.wait_for_timeout(300)


def _neutralize_fixed_nav_for_capture(page) -> None:
    """CDP's full-page screenshot (Page.captureScreenshot with
    captureBeyondViewport) renders the whole document at once instead of
    compositing a real scrolled viewport, so `position: fixed` elements
    (the locked bottom-nav) land at the *original* viewport's fixed offset
    instead of the true document bottom -- they appear stranded partway
    down the capture. This is a screenshot-tooling artifact, not a real
    rendering bug (a real visitor never sees this), and the locked nav is
    reviewed and approved separately from page content (see
    navigation-lock.md) -- so it is hidden for this capture only, never
    touched in the actual block files."""
    page.add_style_tag(content=".bottom-nav{display:none!important}")


def screenshot(output_dir: Path, shots_dir: Path, slug: str) -> tuple[Path, Path]:
    from playwright.sync_api import sync_playwright

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

    def handler_factory(*args, **kwargs):
        return QuietHandler(*args, directory=str(output_dir), **kwargs)

    with socketserver.TCPServer(("127.0.0.1", 0), handler_factory) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            shots_dir.mkdir(parents=True, exist_ok=True)
            mobile_path = shots_dir / f"{slug}-mobile.png"
            desktop_path = shots_dir / f"{slug}-desktop.png"
            url = f"http://127.0.0.1:{port}/index.html"
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    executable_path="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
                )
                console_errors: list[str] = []

                mobile_ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
                mobile_page = mobile_ctx.new_page()
                mobile_page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                mobile_page.goto(url, wait_until="networkidle")
                _reveal_everything(mobile_page)
                _neutralize_fixed_nav_for_capture(mobile_page)
                mobile_page.screenshot(path=str(mobile_path), full_page=True)
                mobile_ctx.close()

                desktop_ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                desktop_page = desktop_ctx.new_page()
                desktop_page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                desktop_page.goto(url, wait_until="networkidle")
                _reveal_everything(desktop_page)
                _neutralize_fixed_nav_for_capture(desktop_page)
                desktop_page.screenshot(path=str(desktop_path), full_page=True)
                desktop_ctx.close()

                browser.close()
                if console_errors:
                    print("CONSOLE ERRORS:", *console_errors, sep="\n  ")
        finally:
            httpd.shutdown()
    return mobile_path, desktop_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python3 tools/build_draft_preview.py <structure-id> [output-dir] [--screenshots]")
    target = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else ROOT / ".ruos" / "drafts" / target

    standalone_path = build_standalone_html(target, out_dir / f"{target}.html")
    print(f"STANDALONE: {standalone_path}")

    if "--screenshots" in sys.argv:
        build_preview(target, out_dir)
        mobile_shot, desktop_shot = screenshot(out_dir, out_dir, target)
        print(f"MOBILE SCREENSHOT: {mobile_shot}")
        print(f"DESKTOP SCREENSHOT: {desktop_shot}")
