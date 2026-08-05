from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Mapping


_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class VisualDNAError(ValueError):
    """Raised when a visual profile cannot be resolved safely."""


@dataclass(frozen=True)
class VisualDNA:
    id: str
    colors: Mapping[str, str]
    typography: Mapping[str, str]
    geometry: Mapping[str, str]
    effects: Mapping[str, str]
    rhythm: Mapping[str, str]

    def css_variables(self) -> str:
        groups = (self.colors, self.typography, self.geometry, self.effects, self.rhythm)
        declarations = [f"--{key}:{value}" for group in groups for key, value in sorted(group.items())]
        return ":root{" + ";".join(declarations) + "}"

    def fingerprint_payload(self) -> tuple[tuple[str, str], ...]:
        groups = (self.colors, self.typography, self.geometry, self.effects, self.rhythm)
        return tuple((key, value) for group in groups for key, value in sorted(group.items()))


def _rgb(hex_color: str) -> tuple[int, int, int]:
    if not _HEX.fullmatch(hex_color):
        raise VisualDNAError(f"Invalid six-digit hex color: {hex_color}")
    return tuple(int(hex_color[index : index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]


def _luminance(hex_color: str) -> float:
    channels = []
    for channel in _rgb(hex_color):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _profile(
    profile_id: str,
    *,
    colors: Mapping[str, str],
    typography: Mapping[str, str],
    geometry: Mapping[str, str],
    effects: Mapping[str, str],
    rhythm: Mapping[str, str],
) -> VisualDNA:
    required_colors = {"color-bg", "color-surface", "color-ink", "color-muted", "color-accent", "color-accent-ink", "color-line"}
    missing = sorted(required_colors - colors.keys())
    if missing:
        raise VisualDNAError(f"Profile {profile_id} misses color tokens: {', '.join(missing)}")
    for key, value in colors.items():
        if key.startswith("color-"):
            _rgb(value)
    if contrast_ratio(colors["color-ink"], colors["color-bg"]) < 7:
        raise VisualDNAError(f"Profile {profile_id} fails AAA body contrast")
    if contrast_ratio(colors["color-accent-ink"], colors["color-accent"]) < 4.5:
        raise VisualDNAError(f"Profile {profile_id} fails CTA contrast")
    return VisualDNA(
        id=profile_id,
        colors=_freeze(colors),
        typography=_freeze(typography),
        geometry=_freeze(geometry),
        effects=_freeze(effects),
        rhythm=_freeze(rhythm),
    )


_PROFILES = {
    "red-umbrella-v16": _profile(
        "red-umbrella-v16",
        colors={
            "color-bg": "#F4F1EA",
            "color-surface": "#FFFFFF",
            "color-ink": "#17161B",
            "color-muted": "#625E66",
            "color-accent": "#D21E2B",
            "color-accent-ink": "#FFFFFF",
            "color-line": "#D8D1C7",
            "color-dark": "#17161B",
            "color-dark-ink": "#FFFFFF",
            "color-gold": "#C9A227",
        },
        typography={
            "font-display": "'Vazirmatn', 'Noto Sans Arabic', Tahoma, sans-serif",
            "font-body": "'Vazirmatn', 'Noto Sans Arabic', Tahoma, sans-serif",
            "font-size-body": "clamp(1rem,0.96rem + 0.2vw,1.125rem)",
            "font-size-display": "clamp(3rem,8vw,8.75rem)",
            "line-body": "1.9",
            "line-display": "0.98",
            "tracking-display": "-0.045em",
        },
        geometry={
            "content-max": "82rem",
            "copy-max": "68ch",
            "radius-sm": "0.75rem",
            "radius-md": "1.5rem",
            "radius-lg": "2.5rem",
            "header-height": "4.75rem",
        },
        effects={
            "shadow-soft": "0 1.5rem 4rem rgba(23,22,27,.12)",
            "shadow-lift": "0 2rem 6rem rgba(23,22,27,.2)",
            "blur-glass": "18px",
            "ease-emphasis": "cubic-bezier(.22,1,.36,1)",
        },
        rhythm={
            "space-1": "0.5rem",
            "space-2": "1rem",
            "space-3": "1.5rem",
            "space-4": "2.5rem",
            "space-5": "4rem",
            "space-6": "clamp(5rem,12vw,10rem)",
        },
    )
}


def available_profiles() -> tuple[str, ...]:
    return tuple(sorted(_PROFILES))


def resolve_visual_dna(profile_id: str) -> VisualDNA:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        available = ", ".join(available_profiles())
        raise VisualDNAError(f"Unknown visual profile '{profile_id}'. Available: {available}") from exc
