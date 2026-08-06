from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class CreativeRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class RegistryItem:
    id: str
    kind: str
    purpose: str
    use_cases: tuple[str, ...]
    constraints: tuple[str, ...]
    rtl_score: int
    mobile_score: int
    performance_score: int
    accessibility_score: int
    conversion_score: int
    agency_score: int

    @property
    def composite_score(self) -> int:
        weighted = (
            self.rtl_score * 12
            + self.mobile_score * 16
            + self.performance_score * 14
            + self.accessibility_score * 16
            + self.conversion_score * 20
            + self.agency_score * 22
        )
        return round(weighted / 100)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "purpose": self.purpose,
            "use_cases": list(self.use_cases),
            "constraints": list(self.constraints),
            "scores": {
                "rtl": self.rtl_score,
                "mobile": self.mobile_score,
                "performance": self.performance_score,
                "accessibility": self.accessibility_score,
                "conversion": self.conversion_score,
                "agency": self.agency_score,
                "composite": self.composite_score,
            },
        }


class CreativeRegistry:
    def __init__(self, items: Iterable[RegistryItem]) -> None:
        normalized = tuple(sorted(items, key=lambda item: item.id))
        ids = [item.id for item in normalized]
        if len(ids) != len(set(ids)):
            raise CreativeRegistryError("Creative registry contains duplicate ids")
        for item in normalized:
            if not item.id.strip() or not item.kind.strip() or not item.purpose.strip():
                raise CreativeRegistryError("Registry items require id, kind and purpose")
            for score in (
                item.rtl_score,
                item.mobile_score,
                item.performance_score,
                item.accessibility_score,
                item.conversion_score,
                item.agency_score,
            ):
                if not 0 <= score <= 100:
                    raise CreativeRegistryError("Registry scores must be between 0 and 100")
        self._items = normalized

    @property
    def items(self) -> tuple[RegistryItem, ...]:
        return self._items

    def get(self, item_id: str) -> RegistryItem:
        for item in self._items:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    def ranked(self, kind: str, minimum: int = 0) -> tuple[RegistryItem, ...]:
        return tuple(
            sorted(
                (item for item in self._items if item.kind == kind and item.composite_score >= minimum),
                key=lambda item: (-item.composite_score, item.id),
            )
        )


def default_creative_registry() -> CreativeRegistry:
    return CreativeRegistry(
        (
            RegistryItem(
                id="chaptered-visual-story",
                kind="storytelling",
                purpose="Turn a complex decision into memorable editorial chapters.",
                use_cases=("commercial investigation", "high-consideration B2B", "knowledge hub"),
                constraints=("direct information access", "clear chapter purpose", "linear mobile fallback"),
                rtl_score=96,
                mobile_score=91,
                performance_score=94,
                accessibility_score=92,
                conversion_score=88,
                agency_score=95,
            ),
            RegistryItem(
                id="progressive-structural-reveal",
                kind="scroll",
                purpose="Reveal technical depth at the point of user curiosity.",
                use_cases=("product anatomy", "comparison", "spatial explanation"),
                constraints=("no hidden critical content", "reduced-motion fallback", "scroll cues"),
                rtl_score=94,
                mobile_score=90,
                performance_score=88,
                accessibility_score=89,
                conversion_score=82,
                agency_score=93,
            ),
            RegistryItem(
                id="narrative-motion-cues",
                kind="motion",
                purpose="Use motion to signal narrative change and spatial relationships.",
                use_cases=("chapter transitions", "focus change", "structural explanation"),
                constraints=("reduced motion", "no reading obstruction", "budgeted duration"),
                rtl_score=94,
                mobile_score=88,
                performance_score=84,
                accessibility_score=90,
                conversion_score=80,
                agency_score=96,
            ),
            RegistryItem(
                id="decision-path-interaction",
                kind="interaction",
                purpose="Route users from context and objective to the correct commercial action.",
                use_cases=("solution finder", "purchase route", "investment route"),
                constraints=("keyboard support", "announced state", "non-JS fallback"),
                rtl_score=98,
                mobile_score=94,
                performance_score=91,
                accessibility_score=96,
                conversion_score=96,
                agency_score=91,
            ),
        )
    )
