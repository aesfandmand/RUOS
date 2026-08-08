from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SectionSpec:
    id: str
    kind: str
    title: str
    body: str = ""
    eyebrow: str = ""
    cta_label: str = ""
    cta_href: str = ""
    items: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class PageSpec:
    slug: str
    lang: str
    direction: str
    title: str
    description: str
    brand: str
    visual_profile: str
    sections: tuple[SectionSpec, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BuildContext:
    project_root: Path
    output_root: Path
    strict: bool = True
    require_live_research: bool = False
    research_snapshot_root: Path | None = None
    require_search_discovery: bool = False
    discovery_snapshot_root: Path | None = None
    require_competitor_evidence: bool = False
    competitor_snapshot_root: Path | None = None
    require_publish_media: bool = False
    media_bindings_path: Path | None = None
    produce_media_derivatives: bool = False
    media_output_subdir: str = "assets/generated-media"


@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    score: int
    evidence: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildResult:
    page: PageSpec
    output_dir: Path
    files: tuple[Path, ...]
    gates: tuple[GateResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.gates)
