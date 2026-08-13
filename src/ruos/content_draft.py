"""Validate a drafted rich-section content block, and fill real gaps with a
visibly-marked placeholder rather than leaving the page incomplete.

Mirrors ``page_critic.py``'s reporting shape (finding = discipline/severity/
observation/action/evidence) deliberately — this is the same kind of
deterministic, code-based check, just over a content *draft* instead of a
fully composed page. See ``05-rules/website/content-voice-v1.md`` for the
rules this module enforces: every specific claim is either cited to a real,
verified research source or explicitly tagged a placeholder — never a third,
silent option.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .block_composer import BlockCompositionError, _validate_slots
from .block_registry import BlockLibrary, BlockRegistryError
from .research_snapshot import ResearchSnapshot

# The standard Latin placeholder passage — per the owner's explicit
# instruction (2026-08-13), used as-is rather than an invented Persian
# filler: being obviously foreign text in an RTL Persian page is exactly
# what makes it unmissable as "not final," and it is combined with the
# muted `data-placeholder` colour already used across the block library.
LOREM_IPSUM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
    "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
    "occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
    "mollit anim id est laborum."
)

# Which slot inside each block's `items` entries carries the checkable prose.
_TEXT_FIELD_BY_BLOCK = {
    "numbered-features": "body",
    "parts-zigzag": "body",
    "checklist-section": "value",
}

_PERSIAN_LETTERS = re.compile(r"[؀-ۿ]")

# The real, owner-supplied glossary — 05-rules/website/persian-writing-style-v1.html
# §4 (tab ۴), a locked document, not a shortlist invented for this module.
# It is explicitly a living list there; add new entries in that file first,
# then mirror them here so the checker actually catches them.
_BANNED_WORDS = (
    "ما می‌دانیم که", "این بدان معناست که", "به شما کمک می‌کنیم تا",
    "نه تنها", "اجازه دهید", "ما اینجاییم تا", "در دنیای امروز",
    "راهکار جامع", "فول‌سرویس", "تیم متخصص و مجرب", "رضایت مشتری اولویت ماست",
    "بهترین", "برترین", "بی‌نظیر", "منحصربه‌فرد", "انقلابی",
    "تجربه‌ای متفاوت", "همراه شما", "انجام می‌شود", "صورت می‌گیرد",
    "قرار داده می‌شود", "شما می‌توانید", "می‌باشد", "با ما تماس بگیرید",
)
# Two real glossary entries are deliberately NOT mirrored here as plain
# substrings: "جهت" (banned only as the administrative "برای"/"regarding"
# — but it is also the real spec label this engine already renders
# honestly, e.g. hero stats' "جهت: افقی"; a substring match would flag
# real content) and "بیش از ۱۰۰ ..." (the number varies; a real regex for
# "بیش از \d+" would be needed, not a fixed phrase). Both need a smarter
# check than substring matching if this list is ever extended to catch them.


def lorem_ipsum_of_length(target_chars: int) -> str:
    """Trim/repeat the standard passage to roughly the length a real answer
    in this slot would have, cut on a word boundary."""
    target_chars = max(40, target_chars)
    text = LOREM_IPSUM
    while len(text) < target_chars:
        text += " " + LOREM_IPSUM
    if len(text) <= target_chars:
        return text
    cut = text.rfind(" ", 0, target_chars)
    return text[: cut if cut > 0 else target_chars].rstrip(",.;") + "."


@dataclass(frozen=True)
class ContentDraftFinding:
    discipline: str
    severity: str  # "blocker" | "refinement" | "strength"
    observation: str
    evidence: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "discipline": self.discipline,
            "severity": self.severity,
            "observation": self.observation,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ContentDraftReport:
    slug: str
    findings: tuple[ContentDraftFinding, ...]
    blockers: tuple[str, ...]
    placeholder_count: int
    release_recommendation: str  # "ready-for-owner-review" | "rejected"

    def payload(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "findings": [f.payload() for f in self.findings],
            "blockers": list(self.blockers),
            "placeholder_count": self.placeholder_count,
            "release_recommendation": self.release_recommendation,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def report(self) -> str:
        lines = [f"# بررسی پیش‌نویس محتوا: {self.slug}", f"وضعیت: {self.release_recommendation}", ""]
        for finding in self.findings:
            mark = {"blocker": "✗", "refinement": "·", "strength": "✓"}[finding.severity]
            lines.append(f"{mark} [{finding.discipline}] {finding.observation}")
        lines.append(f"\n{self.placeholder_count} آیتم placeholder — پیش از بارگزاری در وردپرس باید با محتوای واقعی جایگزین شوند.")
        return "\n".join(lines)


def fill_draft_gaps(blocks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic, no-judgment pass: any item in a covered block whose
    text field is missing or empty gets a Lorem Ipsum placeholder sized to
    roughly what a real answer in that slot would be (matched against the
    other real items already in the same list, or a sane default), tagged
    `"placeholder": true`. Never touches an item that already has real text
    — this only fills genuine gaps, it does not overwrite a draft."""
    filled: list[dict[str, Any]] = []
    for entry in blocks:
        block_id = entry.get("block")
        field = _TEXT_FIELD_BY_BLOCK.get(block_id)
        data = dict(entry.get("data", {}))
        items = data.get("items")
        if field and isinstance(items, list):
            real_lengths = [len(item[field]) for item in items if str(item.get(field, "")).strip() and not item.get("placeholder")]
            target = max(real_lengths) if real_lengths else 220
            new_items = []
            for item in items:
                item = dict(item)
                if not str(item.get(field, "")).strip():
                    item[field] = lorem_ipsum_of_length(target)
                    item["placeholder"] = True
                new_items.append(item)
            data["items"] = new_items
        filled.append({**entry, "data": data})
    return filled


def _is_placeholder_text(text: str) -> bool:
    return "lorem ipsum" in text.lower()


def validate_draft(
    blocks: Sequence[Mapping[str, Any]],
    snapshot: ResearchSnapshot,
    library: BlockLibrary,
) -> ContentDraftReport:
    findings: list[ContentDraftFinding] = []
    blockers: list[str] = []
    placeholder_count = 0
    covered_source_ids = {item.source_id for item in snapshot.evidence}

    def record(discipline: str, observation: str, evidence: list[str], blocker: bool) -> None:
        severity = "blocker" if blocker else ("refinement" if evidence else "strength")
        findings.append(ContentDraftFinding(discipline, severity, observation, tuple(evidence)))
        if blocker:
            blockers.append(f"{discipline}: {observation}")

    # ── block contract ──────────────────────────────────────────────────
    contract_failures: list[str] = []
    for entry in blocks:
        block_id = str(entry.get("block", ""))
        try:
            contract = library.get(block_id)
            _validate_slots(contract, entry.get("data", {}))
        except BlockCompositionError as exc:
            contract_failures.append(f"{block_id}: {exc}")
        except BlockRegistryError:
            contract_failures.append(f"{block_id}: not a real block in the library")
    record(
        "block-contract",
        "; ".join(contract_failures) if contract_failures else "every drafted block matches its real slot contract",
        contract_failures, blocker=bool(contract_failures),
    )

    # ── citation-or-placeholder ─────────────────────────────────────────
    citation_failures: list[str] = []
    placeholder_dishonesty: list[str] = []
    banned_hits: list[str] = []
    for entry in blocks:
        block_id = str(entry.get("block", ""))
        field = _TEXT_FIELD_BY_BLOCK.get(block_id)
        if not field:
            continue
        for index, item in enumerate(entry.get("data", {}).get("items", []) or []):
            text = str(item.get(field, ""))
            is_placeholder = bool(item.get("placeholder"))
            if is_placeholder:
                placeholder_count += 1
                if not _is_placeholder_text(text):
                    placeholder_dishonesty.append(
                        f"{block_id}[{index}]: tagged placeholder but text does not look like Lorem Ipsum"
                    )
                continue
            if not text.strip():
                continue
            source_id = item.get("source_id")
            if not source_id or source_id not in covered_source_ids:
                citation_failures.append(f"{block_id}[{index}]: real text with no verified source_id")
            for word in _BANNED_WORDS:
                if word in text:
                    banned_hits.append(f"{block_id}[{index}]: unsourced claim word '{word}'")
    record(
        "citation",
        "; ".join(citation_failures) if citation_failures else "every non-placeholder claim cites a verified source",
        citation_failures, blocker=bool(citation_failures),
    )
    record(
        "placeholder-honesty",
        "; ".join(placeholder_dishonesty) if placeholder_dishonesty else "every tagged placeholder is genuinely Lorem Ipsum, never real-looking prose",
        placeholder_dishonesty, blocker=bool(placeholder_dishonesty),
    )
    record(
        "voice",
        "; ".join(banned_hits) if banned_hits else "no unsourced superlatives (content-voice-v1.md §3)",
        banned_hits, blocker=False,
    )

    recommendation = "rejected" if blockers else "ready-for-owner-review"
    slug = snapshot.page_slug
    return ContentDraftReport(
        slug=slug, findings=tuple(findings), blockers=tuple(blockers),
        placeholder_count=placeholder_count, release_recommendation=recommendation,
    )
