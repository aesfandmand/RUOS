from __future__ import annotations

from .models import GateResult, PageSpec


REQUIRED_SEQUENCE = (
    "hero",
    "story",
    "knowledge",
    "interaction",
    "conversion",
)


def evaluate(page: PageSpec, html: str, css: str, runtime: str) -> tuple[GateResult, ...]:
    kinds = [section.kind for section in page.sections]
    text_length = sum(len(section.title) + len(section.body) for section in page.sections)

    checks: list[GateResult] = []

    def gate(name: str, score: int, evidence: list[str], failures: list[str]) -> None:
        checks.append(
            GateResult(
                gate=name,
                passed=not failures and score >= 70,
                score=score,
                evidence=tuple(evidence),
                failures=tuple(failures),
            )
        )

    gate(
        "creative-direction",
        100 if page.visual_profile else 0,
        [f"visual_profile={page.visual_profile}"],
        [] if page.visual_profile else ["visual profile is missing"],
    )
    gate(
        "reading-experience",
        min(100, 50 + text_length // 12),
        [f"content_chars={text_length}"],
        [] if text_length >= 240 else ["content is too thin for a deliberate reading journey"],
    )
    gate(
        "visual-rhythm",
        90 if len(page.sections) >= 5 else 50,
        [f"section_count={len(page.sections)}"],
        [] if len(page.sections) >= 5 else ["fewer than five narrative beats"],
    )
    gate(
        "storytelling",
        90 if "story" in kinds else 40,
        [f"section_kinds={','.join(kinds)}"],
        [] if "story" in kinds else ["story section is missing"],
    )
    gate(
        "interaction",
        85 if "IntersectionObserver" in runtime else 30,
        ["runtime contains progressive section observation"],
        [] if "IntersectionObserver" in runtime else ["interaction runtime is missing"],
    )
    gate(
        "motion",
        85 if "prefers-reduced-motion" in css else 30,
        ["reduced-motion fallback exists"],
        [] if "prefers-reduced-motion" in css else ["motion accessibility fallback is missing"],
    )
    gate(
        "conversion",
        90 if any(section.cta_href for section in page.sections) else 30,
        ["contextual CTA found"],
        [] if any(section.cta_href for section in page.sections) else ["no contextual CTA"],
    )
    seo_failures = []
    if "application/ld+json" not in html:
        seo_failures.append("JSON-LD is missing")
    if not page.description:
        seo_failures.append("meta description is missing")
    gate("seo-ai-seo", 95 if not seo_failures else 40, ["semantic metadata compiled"], seo_failures)
    perf_failures = []
    if len(html.encode("utf-8")) > 120_000:
        perf_failures.append("HTML exceeds Sprint 1 budget")
    if len(css.encode("utf-8")) > 80_000:
        perf_failures.append("CSS exceeds Sprint 1 budget")
    gate("performance", 95 if not perf_failures else 50, ["static asset budgets checked"], perf_failures)

    professional_failures = []
    for required in REQUIRED_SEQUENCE:
        if required not in kinds:
            professional_failures.append(f"missing required creative beat: {required}")
    gate(
        "professional-review",
        max(0, 100 - 15 * len(professional_failures)),
        ["ten-gate policy executed"],
        professional_failures,
    )
    return tuple(checks)
