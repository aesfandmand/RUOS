from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from .github_registry_adapter import GitHubRegistryAdapter, GitHubRegistryError
from .open_source_registry import OpenSourceAsset, OpenSourceRegistry, OpenSourceRegistryError


@dataclass(frozen=True)
class RegistrySeed:
    repository: str
    asset_id: str
    name: str
    category: str
    package_name: str
    scores: tuple[int, int, int, int, int, int, int]
    capabilities: tuple[str, ...]
    constraints: tuple[str, ...] = ()


class RegistryAssetBuilder(Protocol):
    def build_asset(self, repository: str, **kwargs: object) -> OpenSourceAsset: ...


DEFAULT_REGISTRY_SEEDS: tuple[RegistrySeed, ...] = (
    RegistrySeed(
        "lucide-icons/lucide", "lucide", "Lucide", "icon", "lucide",
        (95, 94, 91, 97, 96, 96, 96),
        ("svg", "tree-shaking", "rtl-safe", "framework-agnostic", "stroke-icons"),
        ("Maintain a single stroke weight per experience.",),
    ),
    RegistrySeed(
        "phosphor-icons/core", "phosphor-icons", "Phosphor Icons", "icon", "@phosphor-icons/core",
        (91, 91, 89, 95, 94, 91, 92),
        ("svg", "multiple-weights", "rtl-safe", "framework-agnostic"),
        ("Use one icon weight consistently within a page.",),
    ),
    RegistrySeed(
        "motiondivision/motion", "motion", "Motion", "animation", "motion",
        (94, 94, 93, 94, 91, 95, 95),
        ("web-animations", "scroll", "gestures", "reduced-motion", "tree-shaking"),
        ("Prefer native scroll progress and reduced-motion fallbacks.",),
    ),
    RegistrySeed(
        "darkroomengineering/lenis", "lenis", "Lenis", "scroll", "lenis",
        (90, 88, 82, 92, 85, 92, 90),
        ("smooth-scroll", "raf-control", "anchors", "touch-safe"),
        ("Do not override native scrolling when reduced motion is requested.",),
    ),
    RegistrySeed(
        "radix-ui/primitives", "radix-primitives", "Radix Primitives", "component", "@radix-ui/react-primitive",
        (96, 96, 99, 92, 91, 98, 98),
        ("headless", "keyboard", "aria", "focus-management", "composable"),
        ("Visual styling remains the responsibility of RUOS.",),
    ),
    RegistrySeed(
        "tailwindlabs/headlessui", "headless-ui", "Headless UI", "component", "@headlessui/react",
        (94, 94, 98, 91, 90, 96, 96),
        ("headless", "keyboard", "aria", "react", "vue"),
        ("Use only when the target runtime includes a supported framework.",),
    ),
    RegistrySeed(
        "shadcn-ui/ui", "shadcn-ui", "shadcn/ui", "design-system", "shadcn",
        (96, 95, 95, 90, 88, 99, 97),
        ("source-owned", "radix", "tailwind", "composable", "accessible"),
        ("Avoid default visual appearance; apply project Visual DNA.",),
    ),
    RegistrySeed(
        "radix-ui/colors", "radix-colors", "Radix Colors", "color", "@radix-ui/colors",
        (93, 94, 95, 99, 95, 95, 96),
        ("semantic-scales", "dark-mode", "contrast-aware", "css-variables"),
        ("Validate final token pairings with rendered contrast tests.",),
    ),
    RegistrySeed(
        "dequelabs/axe-core", "axe-core", "axe-core", "accessibility", "axe-core",
        (97, 96, 100, 90, 100, 98, 99),
        ("wcag", "automated-audit", "browser", "ci", "rule-engine"),
        ("Automated results never replace manual accessibility review.",),
    ),
    RegistrySeed(
        "microsoft/playwright", "playwright", "Playwright", "qa", "playwright",
        (99, 98, 94, 91, 88, 100, 100),
        ("browser-automation", "screenshots", "mobile-emulation", "tracing", "ci"),
        ("Pin browser versions in production CI.",),
    ),
    RegistrySeed(
        "fontsource/fontsource", "fontsource", "Fontsource", "font", "@fontsource-variable/inter",
        (95, 96, 90, 94, 90, 98, 97),
        ("self-hosted", "variable-fonts", "subsets", "npm", "privacy"),
        ("Verify Persian glyph coverage before selection.",),
    ),
)


def refresh_open_source_registry(
    adapter: RegistryAssetBuilder | None = None,
    *,
    seeds: Iterable[RegistrySeed] = DEFAULT_REGISTRY_SEEDS,
    minimum_success: int | None = None,
) -> tuple[OpenSourceRegistry, tuple[str, ...]]:
    builder = adapter or GitHubRegistryAdapter()
    seed_items = tuple(seeds)
    if not seed_items:
        raise OpenSourceRegistryError("Registry refresh requires at least one seed")
    required = minimum_success if minimum_success is not None else len(seed_items)
    if required < 1 or required > len(seed_items):
        raise OpenSourceRegistryError("minimum_success must be between 1 and the seed count")

    assets: list[OpenSourceAsset] = []
    failures: list[str] = []
    for seed in seed_items:
        maintenance, documentation, accessibility, performance, rtl, ecosystem, production = seed.scores
        try:
            assets.append(builder.build_asset(
                seed.repository,
                asset_id=seed.asset_id,
                name=seed.name,
                category=seed.category,
                package_name=seed.package_name,
                maintenance_score=maintenance,
                documentation_score=documentation,
                accessibility_score=accessibility,
                performance_score=performance,
                rtl_score=rtl,
                ecosystem_score=ecosystem,
                production_score=production,
                capabilities=seed.capabilities,
                constraints=seed.constraints,
            ))
        except (GitHubRegistryError, OpenSourceRegistryError) as exc:
            failures.append(f"{seed.repository}: {exc}")

    if len(assets) < required:
        detail = "; ".join(failures) or "no assets were accepted"
        raise OpenSourceRegistryError(
            f"Registry refresh accepted {len(assets)} assets; minimum is {required}: {detail}"
        )
    return OpenSourceRegistry.build(assets), tuple(failures)
