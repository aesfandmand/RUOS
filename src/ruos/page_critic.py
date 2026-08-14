"""The design critic: an automated art-director pass over a composed page.

The owner asked for an assistant that reviews every generated page the way
a creative director and an art director would — catching what a human
reviewer catches, before the owner has to. This is that pass.

It is deliberately NOT the older ``design_critic.py`` / ``virtual_studio.py``
/ ``qa.py`` stack. That stack is real and deterministic, but its ``evaluate()``
gate is hard-wired to one legacy page's exact shape: a fixed five-section
kind sequence (``hero, story, knowledge, interaction, conversion``), literal
strings from the old static compiler's output (``"ruos-bottom-nav"``,
``"data-component-variant"``, a specific JSON-LD spacing), and
``PageSpec.metadata`` keys nothing in the block-library pipeline populates.
Bridging it would mean gutting and rewriting its internals anyway, so this
module is a clean rebuild against what the block-library pipeline actually
produces (``block_page.RenderedPage`` / ``block_composer.ComposedPage``),
reusing only the reporting *shape* that stack got right: a finding per
discipline, with severity, a concrete action, and evidence — never a bare
pass/fail with no reason.

Every check here is code, not opinion: it inspects the real rendered HTML,
CSS and script, the source page spec, and the block registry. Nothing here
calls out to a model to "judge" the page — that would be exactly the kind
of unverifiable claim design-model §3 forbids. What this catches is
structural: the rules in 05-rules/website/red-umbrella-design-model-v1.md
that keep getting violated because nothing was checking for them.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .block_composer import ComposedPage
from .block_page import RenderedPage
from .block_registry import BlockLibrary
from .navigation_lock import LOCKED_FILES, UNLOCK_NOTICE

REPO_ROOT = Path(__file__).resolve().parents[2]


class PageCriticError(ValueError):
    """Raised when a critique cannot be produced from the inputs given."""


@dataclass(frozen=True)
class CritiqueFinding:
    discipline: str
    severity: str  # "blocker" | "major" | "refinement" | "strength"
    score: int
    observation: str
    action: str
    evidence: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "discipline": self.discipline,
            "severity": self.severity,
            "score": self.score,
            "observation": self.observation,
            "action": self.action,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class PageCritique:
    page_slug: str
    findings: tuple[CritiqueFinding, ...]
    blockers: tuple[str, ...]
    improvement_backlog: tuple[str, ...]
    release_recommendation: str  # "reject" | "publish-with-backlog" | "publish"
    quality_score: int
    placeholder_count: int

    def payload(self) -> dict[str, Any]:
        return {
            "page_slug": self.page_slug,
            "findings": [f.payload() for f in self.findings],
            "blockers": list(self.blockers),
            "improvement_backlog": list(self.improvement_backlog),
            "release_recommendation": self.release_recommendation,
            "quality_score": self.quality_score,
            "placeholder_count": self.placeholder_count,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def report(self) -> str:
        """A short, human-readable version for a chat reply or a CLI run."""
        lines = [f"# نقد صفحه: {self.page_slug}", f"امتیاز کل: {self.quality_score}/100 — {self.release_recommendation}", ""]
        for finding in self.findings:
            mark = {"blocker": "✗", "major": "▲", "refinement": "·", "strength": "✓"}[finding.severity]
            lines.append(f"{mark} [{finding.discipline}] {finding.score}/100 — {finding.observation}")
            if finding.severity != "strength":
                lines.append(f"   → {finding.action}")
        if self.placeholder_count:
            lines.append(f"\n{self.placeholder_count} مقدار placeholder روی این صفحه — طبق قانون محتوا باید گزارش شود، نه پنهان.")
        return "\n".join(lines)


def _severity(score: int, failures: list[str]) -> str:
    # Severity follows whether there is an actual finding, not an arbitrary
    # headroom below 100 — a check with zero failures is a strength, full
    # stop, or the report cries wolf and nobody trusts the next real one.
    if not failures:
        return "strength"
    if score < 70:
        return "blocker"
    if score < 88:
        return "major"
    return "refinement"


def _score(base: int, failures: list[str], penalty: int = 16) -> int:
    return max(0, min(100, base - penalty * len(failures)))


_DISCIPLINE_ACTIONS = {
    "colour": "Bring the surface back to the palette: white-dominant, cream for contrast, red only as accent, CTA or the glossy/textured finish — never flat, never pink.",
    "navigation": "Restore the locked header and bottom nav unmodified; the navigation does not vary by page.",
    "motion": "Give every entering section a data-reveal (or a masked/zigzag variant) and confirm the reveal driver ships in the runtime.",
    "icons": "Use a real Phosphor icon from the sprite for every content affordance; fix or remove any dangling #icon-* reference.",
    "content-honesty": "Replace invented-looking values with a tagged placeholder, or bring in the real registry data.",
    "images": "Reserve every image slot with real alt text; never collapse a slot because the file is missing.",
    "rhythm": "Break up repeated layouts or surfaces; alternate white/paper and vary composition family section to section.",
    "accessibility": "Restore a single H1, a real heading outline, and visible text on every interactive control.",
    "seo-schema": "Render the JSON-LD graph, a canonical link, and a meta description sized for a real search snippet.",
    "performance": "Trim HTML/CSS/script back under budget before shipping.",
}


def _read_locked(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _count_placeholders(html: str) -> int:
    """Count what actually renders as a placeholder, not what the spec
    happens to tag — a block can mark a value ``"placeholder": true`` in its
    data OR flag it in markup via ``data-placeholder``/``.placeholder-chip``;
    either way, if it does not show up in the rendered HTML it is not
    findable later, which is the actual failure design model §3 cares about.
    """
    return len(re.findall(r"data-placeholder=|class=\"[^\"]*placeholder-chip", html))


def critique_page(
    rendered: RenderedPage,
    spec: Mapping[str, Any],
    library: BlockLibrary,
) -> PageCritique:
    """Review one composed page the way an art/creative director would.

    ``rendered`` is what ``block_page.render_page`` returns; ``spec`` is the
    same page-spec mapping that was rendered (so the critic can see the raw
    data — placeholders, images, shell — not just the HTML string); ``library``
    is the loaded block library (so icon references can be checked against
    the real sprite and block contracts).
    """
    html, css, script = rendered.html, rendered.css, rendered.script
    composed: ComposedPage = rendered.composed
    findings: list[CritiqueFinding] = []
    blockers: list[str] = []
    backlog: list[str] = []

    def record(discipline: str, score: int, observation: str, evidence: list[str], failures: list[str], critical: bool = False) -> None:
        # A "critical" discipline has no graduated severity: the navigation
        # lock is a hard site-wide rule enforced by its own test suite, so
        # any deviation here is a blocker outright, never "graded" to major.
        severity = "blocker" if (critical and failures) else _severity(score, failures)
        findings.append(CritiqueFinding(discipline, severity, score, observation, _DISCIPLINE_ACTIONS[discipline], tuple(evidence)))
        if severity == "blocker":
            blockers.append(f"{discipline}: {observation}")
        elif severity in {"major", "refinement"}:
            backlog.append(f"{discipline}: {_DISCIPLINE_ACTIONS[discipline]}")

    # ── colour ────────────────────────────────────────────────────────────
    # Checked per-block, not on the whole concatenated stylesheet: a blanket
    # substring search over the full CSS false-positives on _tokens' own
    # `--red-soft:#fff0f3` custom-property *definition* (present on purpose,
    # other blocks still reference it) and on the locked nav's own CSS
    # (exempt by the navigation lock, not by this discipline). Small accent
    # marks (a 6px dot, a 3px progress bar, ::selection) are exempt per
    # design model §1 — texture is invisible at that size.
    colour_failures: list[str] = []
    # Only genuinely non-surface uses are exempt now that every real fill in
    # the block library has been converted: ::selection is a text highlight,
    # not a filled surface, and .reading-progress is a 3px bar — the design
    # model's own "too thin for texture" example.
    exempt_selector_hints = ("::selection", "reading-progress")
    for block_id in composed.used_blocks:
        if block_id in {"site-header", "bottom-nav", "_tokens"}:
            continue
        block_css = library.get(block_id).style
        if re.search(r"var\(--red-soft\)", block_css):
            colour_failures.append(f"{block_id}: pink (var(--red-soft)) is used")
        for match in re.finditer(r"([^{}]+)\{[^{}]*\bbackground\s*:\s*var\(--red\)\s*[;}]", block_css):
            selector = match.group(1).strip().splitlines()[-1].strip()
            if any(hint in selector for hint in exempt_selector_hints):
                continue
            colour_failures.append(f"{block_id}: flat var(--red) fill on `{selector}` — should be --red-gloss (see §1)")
    record("colour", _score(100, colour_failures), (
        "; ".join(colour_failures) if colour_failures else "palette matches design model §1: no pink, no flat black, no flat red where glossy belongs"
    ), [f"blocks_checked={len(composed.used_blocks)}"], colour_failures)

    # ── navigation (reuses the same lock the tests enforce) ────────────────
    nav_failures: list[str] = []
    if "site-header" not in composed.used_blocks:
        nav_failures.append("site-header is not part of this page's shell")
    if "bottom-nav" not in composed.used_blocks:
        nav_failures.append("bottom-nav is not part of this page's shell")
    mismatched = []
    for relative_path, expected_hash in LOCKED_FILES.items():
        actual_hash = hashlib.sha256(_read_locked(relative_path).encode("utf-8")).hexdigest()
        if actual_hash != expected_hash:
            mismatched.append(relative_path)
    if mismatched:
        nav_failures.append("locked nav files changed on disk: " + ", ".join(mismatched) + " — " + UNLOCK_NOTICE)
    record("navigation", _score(100, nav_failures), (
        "; ".join(nav_failures) if nav_failures else "site-header and bottom-nav present, and match the locked hashes"
    ), [f"used_blocks={','.join(composed.used_blocks)}"], nav_failures, critical=True)

    # ── motion ───────────────────────────────────────────────────────────
    motion_failures: list[str] = []
    reveal_count = html.count("data-reveal")
    content_block_count = len(composed.blocks)
    if content_block_count and reveal_count == 0:
        motion_failures.append("no [data-reveal] anywhere — the page will read as static")
    if reveal_count and "IntersectionObserver" not in script:
        motion_failures.append("data-reveal markup exists but no IntersectionObserver driver ships in the runtime")
    if "prefers-reduced-motion" not in css:
        motion_failures.append("no prefers-reduced-motion fallback in the composed CSS")
    record("motion", _score(100, motion_failures), (
        "; ".join(motion_failures) if motion_failures else f"{reveal_count} reveal targets, driven by a real observer, with a reduced-motion fallback"
    ), [f"reveal_targets={reveal_count}", f"content_blocks={content_block_count}"], motion_failures)

    # ── icons ────────────────────────────────────────────────────────────
    icon_failures: list[str] = []
    sprite_ids = set(re.findall(r'<symbol id="([^"]+)"', html))
    used_icons = re.findall(r'href="#(icon-[a-z0-9-]+)"', html)
    broken = sorted({name for name in used_icons if name not in sprite_ids})
    if broken:
        icon_failures.append("dangling icon references: " + ", ".join(broken))
    if content_block_count and not used_icons:
        icon_failures.append("content carries zero icon references — check every section actually needs one before treating this as a pass")
    record("icons", _score(100, icon_failures), (
        "; ".join(icon_failures) if icon_failures else f"{len(used_icons)} icon references, all resolve in the sprite"
    ), [f"icon_refs={len(used_icons)}", f"distinct={len(set(used_icons))}"], icon_failures)

    # ── content honesty (design model §3) ───────────────────────────────
    # A placeholder is not itself a failure — the failure is an untagged,
    # suspiciously-precise value the spec has no source for, which is not
    # mechanically detectable from HTML alone. What this checks is the part
    # that is checkable: every placeholder must stay visible and findable,
    # never silently blended in as if it were verified data.
    placeholder_count = _count_placeholders(html)
    record("content-honesty", 100, (
        f"{placeholder_count} placeholder value(s) on this page, each carrying a visible marker"
        if placeholder_count else "no placeholder values on this page"
    ), [f"placeholder_count={placeholder_count}"], [])

    # ── images ───────────────────────────────────────────────────────────
    image_failures: list[str] = []
    empty_slots = len(re.findall(r'<figure class="[^"]*img-slot[^"]*"[^>]*>\s*</figure>', html))
    if empty_slots:
        image_failures.append(f"{empty_slots} image slot(s) render with no image and no fallback copy")
    record("images", _score(100, image_failures), (
        "; ".join(image_failures) if image_failures else "every image slot carries either a real photo or real alt/description copy"
    ), [f"empty_slots={empty_slots}"], image_failures)

    # ── rhythm (block_composer already enforces this at compose time —
    # a successfully composed page has already passed; this just surfaces
    # what it enforced, so the finding is not silently invisible) ─────────
    surfaces = [b.surface for b in composed.blocks]
    layouts = [library.get(b.block_id).layout for b in composed.blocks]
    record("rhythm", 100, (
        f"composer accepted {len(composed.blocks)} sections with no adjacent layout or surface-run violation "
        f"(surfaces: {'→'.join(surfaces)})"
    ), [f"layouts={'→'.join(layouts)}"], [])

    # ── accessibility ────────────────────────────────────────────────────
    a11y_failures: list[str] = []
    h1_count = html.count("<h1")
    if h1_count != 1:
        a11y_failures.append(f"page has {h1_count} <h1> elements, must be exactly 1")
    if re.search(r"<img(?![^>]*\balt=)", html):
        a11y_failures.append("an <img> is missing an alt attribute")
    # A button needs an accessible name, not necessarily visible text — an
    # aria-label (the hero's slide-indicator dots, for one) satisfies this.
    unnamed_buttons = [
        m.group(0) for m in re.finditer(r"<button([^>]*)>\s*</button>", html)
        if "aria-label=" not in m.group(1) and "aria-labelledby=" not in m.group(1)
    ]
    if unnamed_buttons:
        a11y_failures.append(f"{len(unnamed_buttons)} <button> has neither visible text nor an aria-label")
    record("accessibility", _score(100, a11y_failures), (
        "; ".join(a11y_failures) if a11y_failures else f"single H1, every image and button carries real text"
    ), [f"h1_count={h1_count}"], a11y_failures)

    # ── SEO / schema ─────────────────────────────────────────────────────
    seo_failures: list[str] = []
    if "application/ld+json" not in html:
        seo_failures.append("no JSON-LD graph rendered")
    description = str(spec.get("description", ""))
    if not (50 <= len(description) <= 200):
        seo_failures.append(f"meta description is {len(description)} chars, outside the 50–200 snippet range")
    if not spec.get("canonical"):
        seo_failures.append("no canonical URL in the spec")
    if not re.search(r'<html[^>]+lang="[^"]+"[^>]+dir="[^"]+"', html):
        seo_failures.append("<html> is missing lang/dir")
    record("seo-schema", _score(100, seo_failures), (
        "; ".join(seo_failures) if seo_failures else f"schema present, description {len(description)} chars, canonical set"
    ), [f"description_len={len(description)}"], seo_failures)

    # ── performance ──────────────────────────────────────────────────────
    perf_failures: list[str] = []
    html_bytes, css_bytes, script_bytes = len(html.encode()), len(css.encode()), len(script.encode())
    if html_bytes > 180_000:
        perf_failures.append("HTML exceeds the 180KB production budget")
    # The stylesheet carries a base64 @font-face blob (~62KB, over half of it).
    # Budgeting the two together makes this check fire on the font no matter
    # how disciplined the authored CSS is, pointing reviewers at the wrong
    # thing — so they are measured on separate lines and BOTH are reported.
    # The font is still counted, and is a real standing cost worth moving out
    # of the stylesheet; it just no longer masks (or is masked by) real bloat.
    embedded_font_bytes = sum(len(b) for b in re.findall(r"base64,([A-Za-z0-9+/=]+)", css))
    authored_css_bytes = css_bytes - embedded_font_bytes
    if authored_css_bytes > 120_000:
        perf_failures.append("authored CSS exceeds the 120KB production budget")
    if embedded_font_bytes > 70_000:
        perf_failures.append("embedded font data exceeds 70KB — move it out of the stylesheet")
    if script_bytes > 90_000:
        perf_failures.append("script exceeds the 90KB production budget (vendored libraries excluded, they are separate assets)")
    record("performance", _score(100, perf_failures), (
        "; ".join(perf_failures) if perf_failures else
        f"html={html_bytes}B css={authored_css_bytes}B authored +{embedded_font_bytes}B embedded font, "
        f"script={script_bytes}B, within budget"
    ), [f"html_bytes={html_bytes}", f"authored_css_bytes={authored_css_bytes}",
        f"embedded_font_bytes={embedded_font_bytes}", f"script_bytes={script_bytes}"], perf_failures)

    total = round(sum(f.score for f in findings) / len(findings)) if findings else 0
    release = "reject" if blockers else "publish-with-backlog" if backlog else "publish"
    return PageCritique(
        page_slug=str(spec.get("slug", rendered.slug)),
        findings=tuple(findings),
        blockers=tuple(blockers),
        improvement_backlog=tuple(dict.fromkeys(backlog)),
        release_recommendation=release,
        quality_score=total,
        placeholder_count=placeholder_count,
    )
