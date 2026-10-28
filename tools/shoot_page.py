#!/usr/bin/env python3
"""Compose any hand-authored page spec and screenshot it at both breakpoints.

    python3 tools/shoot_page.py <slug> [--spec-root pages/drafts] [--out .ruos/shots]
                                [--viewports] [--standalone]

build_draft_preview.py does this for *structure* pages, which build
themselves from the registry. Hub pages (services, portfolio) are hand-
authored specs, and there was no repeatable way to look at one: every
session wrote a throwaway Playwright script. This is that script, once.

Writes, under <out>/<slug>/:
  * the composed page (index.html + assets/), served over HTTP -- never
    file://, where module scripts are CORS-blocked and every check is void
  * <slug>-mobile.png and <slug>-desktop.png, full page, reveals settled
  * with --viewports, one capture per screen height while really scrolling,
    so motion that depends on scroll position is seen as a visitor sees it
  * with --standalone, a single self-contained <slug>.html the owner can
    open, resize and interact with
Console errors from both breakpoints are printed; a non-empty list exits 1.
"""
from __future__ import annotations

import argparse
import base64
import http.server
import re
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from ruos.block_page import render_page  # noqa: E402
from ruos.block_registry import load_library  # noqa: E402
from ruos.cli import _write_composed_page, load_block_spec  # noqa: E402
from build_draft_preview import _neutralize_fixed_nav_for_capture, _reveal_everything  # noqa: E402

BREAKPOINTS = {"mobile": (390, 844), "desktop": (1440, 900)}


def compose(slug: str, spec_root: Path, out_dir: Path):
    library = load_library()
    spec = load_block_spec(spec_root / f"{slug}.json")
    page = render_page(spec, library)
    _write_composed_page(page, library, out_dir, spec)
    return page


def standalone(page, out_path: Path) -> Path:
    html = page.html.replace('<link rel="stylesheet" href="assets/styles.css">', f"<style>{page.css}</style>")
    script = page.script
    for match in re.findall(r'from\s+["\'](\./[^"\']+\.mjs)["\']', script):
        name = match.split("/")[-1]
        vendor = next(ROOT.glob(f"blocks/*/assets/{name}"))
        script = script.replace(f'"{match}"', '"data:text/javascript;base64,'
                                + base64.b64encode(vendor.read_bytes()).decode("ascii") + '"')
    for tag in ('<script type="module" src="assets/behavior.js"></script>',
                '<script src="assets/behavior.js" defer></script>'):
        html = html.replace(tag, f'<script type="module">{script}</script>')
    logo = ROOT / "blocks" / "site-header" / "assets" / "logo.png"
    html = html.replace('src="assets/logo.png"',
                        'src="data:image/png;base64,' + base64.b64encode(logo.read_bytes()).decode("ascii") + '"')
    # the page's own media (spec "media"), inlined so the file stands alone
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    for name in set(re.findall(r'(?:src|href)="assets/([^"]+)"', html)):
        f = out_path.parent / "assets" / name
        if f.is_file() and f.suffix.lower() in mime:
            uri = f"data:{mime[f.suffix.lower()]};base64," + base64.b64encode(f.read_bytes()).decode("ascii")
            html = html.replace(f'"assets/{name}"', f'"{uri}"')
    out_path.write_text(html, encoding="utf-8")
    return out_path


def shoot(out_dir: Path, slug: str, viewports: bool, limit: int = 40, full: bool = True) -> list[str]:
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

    errors: list[str] = []
    with socketserver.TCPServer(("127.0.0.1", 0), lambda *a, **k: Quiet(*a, directory=str(out_dir), **k)) as httpd:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                for name, (w, h) in BREAKPOINTS.items():
                    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
                    page = ctx.new_page()
                    page.on("console", lambda m, n=name: errors.append(f"[{n}] {m.text}") if m.type == "error" else None)
                    page.on("pageerror", lambda e, n=name: errors.append(f"[{n}] {e}"))
                    page.goto(url, wait_until="networkidle")
                    page.wait_for_timeout(600)
                    if viewports:
                        total = page.evaluate("document.documentElement.scrollHeight")
                        y, i = 0, 0
                        while y < total and i < limit:
                            page.evaluate(f"window.scrollTo(0,{y})")
                            page.wait_for_timeout(700)
                            page.screenshot(path=str(out_dir / f"{slug}-{name}-v{i:02d}.png"))
                            y += h
                            i += 1
                        page.evaluate("window.scrollTo(0,0)")
                    if full:
                        _reveal_everything(page)
                        _neutralize_fixed_nav_for_capture(page)
                        page.screenshot(path=str(out_dir / f"{slug}-{name}.png"), full_page=True)
                    ctx.close()
                browser.close()
        finally:
            httpd.shutdown()
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--spec-root", default="pages/drafts")
    ap.add_argument("--out", default=".ruos/shots")
    ap.add_argument("--viewports", action="store_true")
    ap.add_argument("--standalone", action="store_true")
    ap.add_argument("--limit", type=int, default=40, help="max viewport captures per breakpoint")
    ap.add_argument("--no-full", action="store_true", help="skip the full-page capture")
    args = ap.parse_args()

    out_dir = ROOT / args.out / args.slug
    page = compose(args.slug, ROOT / args.spec_root, out_dir)
    if args.standalone:
        print("STANDALONE:", standalone(page, out_dir / f"{args.slug}.html"))
    errors = shoot(out_dir, args.slug, args.viewports, args.limit, not args.no_full)
    print("SHOTS:", out_dir)
    if errors:
        print("CONSOLE ERRORS:", *errors, sep="\n  ")
        return 1
    print("CONSOLE: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
