from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable


@dataclass
class GateResult:
    id: str
    name: str
    passed: bool
    score: int
    message: str
    hard: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _has(spec: dict[str, Any], path: str) -> bool:
    node: Any = spec
    for part in path.split('.'):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return node not in (None, '', [], {})


def evaluate(spec: dict[str, Any]) -> list[GateResult]:
    checks: list[tuple[str, str, Callable[[dict[str, Any]], bool], str, bool]] = [
        ('G01', 'Creative Direction', lambda s: _has(s, 'creative_direction.idea') and _has(s, 'creative_direction.distinctive_device'), 'صفحه باید ایده مرکزی و ابزار بصری متمایز داشته باشد.', True),
        ('G02', 'Reading Experience', lambda s: len(s.get('sections', [])) >= 6 and _has(s, 'reading_experience.rhythm'), 'ریتم خوانش، تنوع بخش‌ها و مکث‌های روایی الزامی است.', True),
        ('G03', 'Visual Rhythm', lambda s: _has(s, 'visual_dna.spacing_scale') and _has(s, 'visual_dna.typography'), 'فاصله‌گذاری و تایپوگرافی باید از Visual DNA بیاید.', True),
        ('G04', 'Storytelling', lambda s: all(k in s.get('story', {}) for k in ('opening', 'tension', 'resolution')), 'روایت باید آغاز، تنش و حل داشته باشد.', True),
        ('G05', 'Interaction', lambda s: len(s.get('interactions', [])) >= 2, 'حداقل دو تعامل هدفمند لازم است.', False),
        ('G06', 'Motion', lambda s: any(m.get('purpose') and m.get('fallback') for m in s.get('motion', [])), 'هر موشن باید هدف و fallback داشته باشد.', False),
        ('G07', 'Conversion', lambda s: _has(s, 'conversion.primary_cta') and _has(s, 'conversion.trust_path'), 'CTA و مسیر اعتماد باید روشن باشد.', True),
        ('G08', 'SEO + AI SEO', lambda s: _has(s, 'seo.title') and _has(s, 'seo.description') and len(s.get('faq', [])) >= 5, 'عنوان، توضیح و حداقل پنج FAQ لازم است.', True),
        ('G09', 'Performance', lambda s: s.get('performance', {}).get('js_budget_kb', 999) <= 80 and s.get('performance', {}).get('motion_respects_reduced', False), 'بودجه JS و reduced-motion باید رعایت شود.', True),
        ('G10', 'Professional Review', lambda s: _has(s, 'review.owner') and s.get('review', {}).get('minimum_score', 0) >= 80, 'مالک بازبینی و حداقل امتیاز حرفه‌ای باید ثبت شود.', True),
        ('G11', 'Visual DNA Source', lambda s: _has(s, 'visual_dna.source'), 'منبع واقعی Visual DNA، مانند فایل v16، الزامی است.', True),
    ]

    results: list[GateResult] = []
    for gate_id, name, test, failure, hard in checks:
        passed = bool(test(spec))
        results.append(GateResult(gate_id, name, passed, 100 if passed else 0, 'قبول' if passed else failure, hard))
    return results


def hard_failures(results: list[GateResult]) -> list[GateResult]:
    return [result for result in results if result.hard and not result.passed]
