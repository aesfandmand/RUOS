from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from .models import PageSpec


class VoiceStudioError(ValueError):
    """Raised when no approved, page-appropriate content voice is available."""


@dataclass(frozen=True)
class VoiceCandidate:
    id: str
    label: str
    description: str
    sentence_rhythm: str
    vocabulary: str
    persuasion_style: str
    suitable_for: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "sentence_rhythm": self.sentence_rhythm,
            "vocabulary": self.vocabulary,
            "persuasion_style": self.persuasion_style,
            "suitable_for": list(self.suitable_for),
        }


@dataclass(frozen=True)
class VoiceDecision:
    page_slug: str
    language: str
    candidates: tuple[VoiceCandidate, ...]
    approved_voice_id: str
    approval_status: str
    approval_source: str

    @property
    def approved(self) -> VoiceCandidate:
        for candidate in self.candidates:
            if candidate.id == self.approved_voice_id:
                return candidate
        raise VoiceStudioError(f"Approved voice '{self.approved_voice_id}' is not a candidate")

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "language": self.language,
            "candidates": [candidate.payload() for candidate in self.candidates],
            "approved_voice_id": self.approved_voice_id,
            "approval_status": self.approval_status,
            "approval_source": self.approval_source,
            "approved_voice": self.approved.payload(),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_DEFAULT_PERSIAN_VOICES = (
    VoiceCandidate(
        id="strategic-editorial-fa",
        label="راهبردی و تحریریه‌ای",
        description="روان، دقیق و تصمیم‌ساز؛ مناسب مدیران و مخاطبان حرفه‌ای بدون لحن اداری خشک.",
        sentence_rhythm="ترکیب جمله‌های کوتاه برای تأکید و جمله‌های متوسط برای توضیح",
        vocabulary="فارسی معاصر، روشن و حرفه‌ای با حداقل واژه بیگانه",
        persuasion_style="اعتمادسازی با شفافیت، مقایسه و مسئولیت‌پذیری",
        suitable_for=("b2b", "commercial-investigation", "high-consideration"),
    ),
    VoiceCandidate(
        id="human-conversational-fa",
        label="انسانی و گفت‌وگومحور",
        description="صمیمی اما حرفه‌ای؛ نزدیک به گفت‌وگوی یک مشاور باتجربه با مشتری ایرانی.",
        sentence_rhythm="جمله‌های کوتاه و متوسط با پرسش‌های طبیعی",
        vocabulary="روزمره کنترل‌شده، بدون لحن شبکه اجتماعی یا اغراق",
        persuasion_style="کاهش اصطکاک با همدلی و پاسخ روشن به نگرانی‌ها",
        suitable_for=("consultation", "service", "mixed-audience"),
    ),
    VoiceCandidate(
        id="authoritative-technical-fa",
        label="معتبر و فنی",
        description="دقیق و مستند؛ مناسب بخش‌هایی که تصمیم به داده، استاندارد و جزئیات فنی وابسته است.",
        sentence_rhythm="جمله‌های متوسط، ساختار منطقی و نتیجه‌گیری صریح",
        vocabulary="اصطلاحات تخصصی فقط همراه با توضیح قابل‌فهم",
        persuasion_style="اقناع با معیار، شواهد و محدودیت‌های واقعی",
        suitable_for=("technical", "procurement", "institutional"),
    ),
)

# Human-approved decisions persisted independently from page copy so content edits cannot
# accidentally erase the approval gate. New pages remain blocked until explicitly added.
_APPROVED_PAGE_VOICES: Mapping[str, str] = {
    "structures": "strategic-editorial-fa",
}


def select_voice(page: PageSpec) -> VoiceDecision:
    raw = page.metadata.get("voice")
    if isinstance(raw, Mapping):
        approved_voice_id = str(raw.get("approved_voice_id", "")).strip()
        approval_status = str(raw.get("approval_status", "")).strip().lower()
        approval_source = "page-metadata"
    else:
        approved_voice_id = _APPROVED_PAGE_VOICES.get(page.slug, "")
        approval_status = "approved" if approved_voice_id else "pending"
        approval_source = "studio-approval-registry"

    if approval_status != "approved" or not approved_voice_id:
        raise VoiceStudioError("Content production is blocked until a voice candidate is approved")
    decision = VoiceDecision(
        page_slug=page.slug,
        language=page.lang,
        candidates=_DEFAULT_PERSIAN_VOICES,
        approved_voice_id=approved_voice_id,
        approval_status=approval_status,
        approval_source=approval_source,
    )
    decision.approved
    return decision
