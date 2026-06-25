from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import MemoryFact
from backend.app.services.pain_text import has_explicit_no_pain_statement, has_pain_or_injury_signal
from backend.app.services.text_normalization import normalize_user_text


SAFETY_FACT_TYPES = {"allergy", "medical", "injury", "restriction_nutrition"}

_ALLERGY_MARKERS = ("allergic", "allergy", "\u05d0\u05dc\u05e8\u05d2\u05d9", "\u05d0\u05dc\u05e8\u05d2\u05d9\u05d4")
_MEDICAL_MARKERS = (
    "diabetes",
    "asthma",
    "blood pressure",
    "medication",
    "\u05e1\u05d5\u05db\u05e8\u05ea",
    "\u05d0\u05e1\u05ea\u05de\u05d4",
    "\u05dc\u05d7\u05e5 \u05d3\u05dd",
    "\u05ea\u05e8\u05d5\u05e4\u05d4",
    "\u05ea\u05e8\u05d5\u05e4\u05d5\u05ea",
    "\u05d4\u05e8\u05d9\u05d5\u05df",
    "\u05d1\u05d4\u05e8\u05d9\u05d5\u05df",
    "\u05de\u05d7\u05dc\u05d4",
)
_NUTRITION_RESTRICTION_MARKERS = (
    "vegan",
    "vegetarian",
    "kosher",
    "i do not eat",
    "i don't eat",
    "\u05d8\u05d1\u05e2\u05d5\u05e0\u05d9",
    "\u05d8\u05d1\u05e2\u05d5\u05e0\u05d9\u05ea",
    "\u05e6\u05de\u05d7\u05d5\u05e0\u05d9",
    "\u05e6\u05de\u05d7\u05d5\u05e0\u05d9\u05ea",
    "\u05db\u05e9\u05e8",
)
_GENERIC_HEBREW_NOT_EAT_MARKERS = ("\u05dc\u05d0 \u05d0\u05d5\u05db\u05dc", "\u05dc\u05d0 \u05d0\u05d5\u05db\u05dc\u05ea")
_NUTRITION_RESTRICTION_CONTEXT = (
    "\u05d2\u05dc\u05d5\u05d8\u05df",
    "\u05dc\u05e7\u05d8\u05d5\u05d6",
    "\u05de\u05d5\u05e6\u05e8\u05d9 \u05d7\u05dc\u05d1",
    "\u05d7\u05dc\u05d1 \u05d5\u05de\u05d5\u05e6\u05e8\u05d9\u05d5",
    "\u05d1\u05e9\u05e8",
    "\u05e2\u05d5\u05e3",
    "\u05d3\u05d2",
    "\u05d3\u05d2\u05d9\u05dd",
    "\u05d1\u05d9\u05e6\u05d9\u05dd",
    "\u05d1\u05d9\u05e6\u05d4",
    "\u05d1\u05d5\u05d8\u05e0\u05d9\u05dd",
    "\u05d0\u05d2\u05d5\u05d6\u05d9\u05dd",
    "\u05e1\u05d5\u05db\u05e8",
    "\u05e4\u05d7\u05de\u05d9\u05de\u05d5\u05ea",
    "\u05d7\u05d6\u05d9\u05e8",
)
_INJURY_MARKERS = (
    "pain",
    "injury",
    "injured",
    "sharp pain",
    "\u05db\u05d0\u05d1",
    "\u05db\u05d5\u05d0\u05d1",
    "\u05e4\u05e6\u05d9\u05e2\u05d4",
    "\u05e0\u05e4\u05e6\u05e2\u05ea\u05d9",
    "\u05e0\u05d9\u05ea\u05d5\u05d7",
)
_NEGATED_OR_HYPOTHETICAL = (
    "not allergic",
    "no allergy",
    "if i were allergic",
    "\u05dc\u05d0 \u05d0\u05dc\u05e8\u05d2\u05d9",
    "\u05d0\u05d9\u05df \u05dc\u05d9 \u05d0\u05dc\u05e8\u05d2",
    "\u05d0\u05dd \u05d4\u05d9\u05d9\u05ea\u05d9 \u05d0\u05dc\u05e8\u05d2",
)


@dataclass(frozen=True)
class MemoryCandidate:
    fact_type: str
    text_he: str
    confidence: str = "medium"
    salience: float = 1.0
    source_message_id: int | None = None
    safety_event_id: int | None = None


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def process_user_message(
        self,
        *,
        user_id: int,
        text: str,
        source_message_id: int | None = None,
        safety_event_id: int | None = None,
    ) -> list[MemoryFact]:
        return self.reconcile(
            user_id=user_id,
            candidates=self.extract_safety_candidates(
                text,
                source_message_id=source_message_id,
                safety_event_id=safety_event_id,
            ),
        )

    def extract_safety_candidates(
        self,
        text: str,
        *,
        source_message_id: int | None = None,
        safety_event_id: int | None = None,
    ) -> list[MemoryCandidate]:
        normalized = normalize_user_text(text)
        negated_or_hypothetical_allergy = _contains_any(normalized, _NEGATED_OR_HYPOTHETICAL)

        candidates: list[MemoryCandidate] = []
        if _contains_any(normalized, _ALLERGY_MARKERS) and not negated_or_hypothetical_allergy:
            candidates.append(self._candidate("allergy", text, source_message_id, safety_event_id, "high"))
        if _contains_any(normalized, _MEDICAL_MARKERS):
            candidates.append(self._candidate("medical", text, source_message_id, safety_event_id, "high"))
        pain_signal = has_pain_or_injury_signal(normalized)
        injury_marker_signal = _contains_any(normalized, _INJURY_MARKERS)
        if (pain_signal or injury_marker_signal) and not (
            has_explicit_no_pain_statement(normalized) and not pain_signal
        ):
            candidates.append(self._candidate("injury", text, source_message_id, safety_event_id, "medium"))
        has_generic_hebrew_not_eat = _contains_any(normalized, _GENERIC_HEBREW_NOT_EAT_MARKERS)
        has_nutrition_restriction = _contains_any(normalized, _NUTRITION_RESTRICTION_MARKERS) or (
            has_generic_hebrew_not_eat and _contains_any(normalized, _NUTRITION_RESTRICTION_CONTEXT)
        )
        if has_nutrition_restriction:
            candidates.append(
                self._candidate(
                    "restriction_nutrition",
                    text,
                    source_message_id,
                    safety_event_id,
                    "high",
                )
            )
        return candidates

    def reconcile(self, *, user_id: int, candidates: list[MemoryCandidate]) -> list[MemoryFact]:
        saved: list[MemoryFact] = []
        for candidate in candidates:
            if candidate.fact_type not in SAFETY_FACT_TYPES:
                continue
            duplicate = self._find_duplicate(user_id=user_id, candidate=candidate)
            if duplicate is not None:
                duplicate.salience = max(float(duplicate.salience or 0), candidate.salience)
                saved.append(duplicate)
                continue

            fact = MemoryFact(
                user_id=user_id,
                fact_type=candidate.fact_type,
                status="active",
                text_he=_trim_text(candidate.text_he),
                confidence=candidate.confidence,
                salience=candidate.salience,
                source="sync_safety",
                source_message_id=candidate.source_message_id,
                safety_event_id=candidate.safety_event_id,
                valid_at=datetime.now(timezone.utc),
                provenance_json={"extractor": "deterministic_safety_v1"},
                metadata_json={},
            )
            self.db.add(fact)
            saved.append(fact)
        self.db.commit()
        for fact in saved:
            self.db.refresh(fact)
        return saved

    def for_context(self, *, user_id: int, intent: str | None = None) -> dict[str, list[dict[str, Any]]]:
        del intent
        facts = self.db.scalars(
            select(MemoryFact)
            .where(
                MemoryFact.user_id == user_id,
                MemoryFact.status == "active",
                MemoryFact.fact_type.in_(SAFETY_FACT_TYPES),
            )
            .order_by(desc(MemoryFact.salience), desc(MemoryFact.created_at), desc(MemoryFact.id))
        ).all()
        return {"safety": [self.serialize(fact) for fact in facts]}

    @staticmethod
    def serialize(fact: MemoryFact) -> dict[str, Any]:
        return {
            "type": fact.fact_type,
            "text_he": fact.text_he,
            "confidence": fact.confidence,
        }

    @staticmethod
    def _candidate(
        fact_type: str,
        text: str,
        source_message_id: int | None,
        safety_event_id: int | None,
        confidence: str,
    ) -> MemoryCandidate:
        return MemoryCandidate(
            fact_type=fact_type,
            text_he=text,
            confidence=confidence,
            source_message_id=source_message_id,
            safety_event_id=safety_event_id,
        )

    def _find_duplicate(self, *, user_id: int, candidate: MemoryCandidate) -> MemoryFact | None:
        normalized_candidate = _normalize_fact_text(candidate.text_he)
        active = self.db.scalars(
            select(MemoryFact).where(
                MemoryFact.user_id == user_id,
                MemoryFact.fact_type == candidate.fact_type,
                MemoryFact.status == "active",
            )
        ).all()
        return next((fact for fact in active if _normalize_fact_text(fact.text_he) == normalized_candidate), None)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _normalize_fact_text(text: str) -> str:
    return " ".join(normalize_user_text(text).split())


def _trim_text(text: str) -> str:
    return " ".join(text.split())[:1200]
