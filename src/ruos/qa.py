from __future__ import annotations

import re

from .models import GateResult, PageSpec


REQUIRED_SEQUENCE = ("hero", "story", "knowledge", "interaction", "conversion")


def _score(base: int, failures: list[str], penalty: int = 18) -> int:
    return max(0, min(100, base - penalty * len(failures)))


def evaluate(page: PageSpec, html: str, css: str, runtime: str) -> tuple[GateResult, ...]:
    kinds = [section.kind for section in page.sections]
    text_length = sum(len(section.title) + len(section.body) for section in page.sections)
    checks: list[GateResult] = []

    def gate(name: str, score: int, evidence: list[str], failures: list[str]) -> None:
        checks.append(GateResult(gate=name, passed=not failures and score >= 70, score=score, evidence=tuple(evidence), failures=tuple(failures)))

    creative_failures: list[str] = []
    if not page.visual_profile:
        creative_failures.append("visual profile is missing")
    if "data-component-variant" not in html:
        creative_failures.append("resolved component variants are not rendered")
    if len(set(kinds)) < 5:
        creative_failures.append("creative sequence lacks sufficient variation")
    gate("creative-direction", _score(100, creative_failures), [f"visual_profile={page.visual_profile}", f"section_kinds={','.join(kinds)}"], creative_failures)

    reading_failures: list[str] = []
    heading_count = html.count("<h1") + html.count("<h2")
    if text_length < 240:
        reading_failures.append("content is too thin for a deliberate reading journey")
    if heading_count != len(page.sections):
        reading_failures.append("document heading structure does not map one-to-one to sections")
    if html.count("<h2") < 5:
        reading_failures.append("document lacks a complete primary heading sequence")
    gate("reading-experience", _score(min(100, 70 + text_length // 20), reading_failures), [f"content_chars={text_length}", f"heading_count={heading_count}"], reading_failures)

    rhythm_failures: list[str] = []
    if kinds != list(REQUIRED_SEQUENCE):
        rhythm_failures.append("narrative beats are missing or out of order")
    if "ruos-bottom-nav" not in html or "@media(max-width:900px)" not in css:
        rhythm_failures.append("responsive mobile composition is incomplete")
    gate("visual-rhythm", _score(96, rhythm_failures), [f"section_count={len(page.sections)}", "desktop and mobile compositions inspected"], rhythm_failures)

    story_failures: list[str] = []
    if "story" not in kinds:
        story_failures.append("story section is missing")
    if not any(term in page.sections[1].body for term in ("نتیجه", "شروع", "انتخاب", "پیوند")):
        story_failures.append("story beat lacks a clear causal bridge")
    gate("storytelling", _score(94, story_failures), ["narrative bridge and sequence checked"], story_failures)

    interaction_failures: list[str] = []
    if "IntersectionObserver" not in runtime:
        interaction_failures.append("progressive section observation is missing")
    if "aria-pressed" not in runtime or "aria-live" not in html:
        interaction_failures.append("interactive state is not exposed accessibly")
    if "button" not in html:
        interaction_failures.append("decision interaction has no operable controls")
    gate("interaction-accessibility", _score(96, interaction_failures), ["keyboard controls, live output and observer runtime checked"], interaction_failures)

    motion_failures: list[str] = []
    if "prefers-reduced-motion" not in css or "reduceMotion" not in runtime:
        motion_failures.append("reduced-motion policy is incomplete")
    if "target.animate" not in runtime:
        motion_failures.append("motion plan is not executed by runtime")
    gate("motion", _score(95, motion_failures), ["runtime motion and reduced-motion fallback checked"], motion_failures)

    conversion_failures: list[str] = []
    ctas = [section for section in page.sections if section.cta_href and section.cta_label]
    if len(ctas) < 2:
        conversion_failures.append("sales journey requires contextual and closing CTAs")
    if not page.metadata.get("primary_conversion"):
        conversion_failures.append("primary conversion goal is missing")
    if not page.sections[-1].cta_href:
        conversion_failures.append("closing conversion action is missing")
    gate("conversion", _score(97, conversion_failures), [f"cta_count={len(ctas)}", f"primary_conversion={page.metadata.get('primary_conversion', '')}"], conversion_failures)

    seo_failures: list[str] = []
    if "application/ld+json" not in html:
        seo_failures.append("JSON-LD is missing")
    if not page.description or not 70 <= len(page.description) <= 180:
        seo_failures.append("meta description must be between 70 and 180 characters")
    if not page.metadata.get("pillar"):
        seo_failures.append("primary query pillar is missing")
    if '<meta name="description"' not in html or "<title>" not in html:
        seo_failures.append("search title or description is not rendered")
    gate("seo-query-alignment", _score(98, seo_failures), [f"pillar={page.metadata.get('pillar', '')}", "metadata and structured data compiled"], seo_failures)

    ai_failures: list[str] = []
    if "application/ld+json" not in html:
        ai_failures.append("machine-readable schema is missing")
    if not all(section.id for section in page.sections):
        ai_failures.append("stable semantic section identifiers are missing")
    item_titles = [str(item.get("title", "")).strip() for section in page.sections for item in section.items]
    if len([value for value in item_titles if value]) < 3:
        ai_failures.append("entity coverage is insufficient for extraction")
    if not re.search(r'<html[^>]+lang="[^"]+"[^>]+dir="[^"]+"', html):
        ai_failures.append("language and direction metadata are incomplete")
    gate("ai-readiness", _score(96, ai_failures), [f"extractable_entities={len([v for v in item_titles if v])}", "semantic sections and language metadata checked"], ai_failures)

    perf_failures: list[str] = []
    html_size = len(html.encode("utf-8"))
    css_size = len(css.encode("utf-8"))
    runtime_size = len(runtime.encode("utf-8"))
    if html_size > 120_000:
        perf_failures.append("HTML exceeds production budget")
    if css_size > 80_000:
        perf_failures.append("CSS exceeds production budget")
    if runtime_size > 70_000:
        perf_failures.append("runtime exceeds production budget")
    gate("performance", _score(97, perf_failures), [f"html_bytes={html_size}", f"css_bytes={css_size}", f"runtime_bytes={runtime_size}"], perf_failures)

    return tuple(checks)
