"""Strict source-token normalization for Phase 0 contracts.

This module intentionally refuses unknown and negative count tokens. It does not perform
imputation and never maps missing values to numeric zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


ALLOWED_STATUSES = {
    "observed",
    "observed_zero",
    "imputed",
    "suppressed",
    "aggregation_destination",
    "not_public",
    "not_surveyed",
    "not_applicable",
    "source_absent",
    "duplicate_on_other_record",
    "station_absent",
    "outside_scope",
    "invalid",
}


@dataclass(frozen=True)
class NormalizedObservation:
    raw_value: Optional[str]
    numeric_value: Optional[Decimal]
    status: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"Unknown observation status: {self.status}")
        if self.status == "observed_zero" and self.numeric_value != Decimal("0"):
            raise ValueError("observed_zero requires numeric zero")
        if self.status == "observed" and (
            self.numeric_value is None or self.numeric_value <= 0
        ):
            raise ValueError("observed requires a positive numeric value")
        unavailable = {
            "suppressed",
            "not_public",
            "not_surveyed",
            "not_applicable",
            "source_absent",
            "duplicate_on_other_record",
            "station_absent",
            "outside_scope",
            "invalid",
        }
        if self.status in unavailable and self.numeric_value is not None:
            raise ValueError(f"{self.status} must not carry a numeric value")


def _raw_text(raw_value: object) -> Optional[str]:
    if raw_value is None:
        return None
    return str(raw_value).strip()


def normalize_estat_count(raw_value: object) -> NormalizedObservation:
    """Normalize common e-Stat count tokens without inventing values."""

    raw = _raw_text(raw_value)
    if raw in (None, ""):
        return NormalizedObservation(raw, None, "source_absent")
    if raw.upper() == "X":
        return NormalizedObservation(raw, None, "suppressed")
    if raw == "...":
        return NormalizedObservation(raw, None, "not_surveyed")
    if raw == "-":
        return NormalizedObservation(raw, None, "not_applicable")
    normalized_numeric = raw.replace(",", "")
    try:
        value = Decimal(normalized_numeric)
    except InvalidOperation as exc:
        raise ValueError(f"Unrecognized e-Stat count token: {raw!r}") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"Invalid non-finite/negative count: {raw!r}")
    status = "observed_zero" if value == 0 else "observed"
    return NormalizedObservation(raw, value, status)


def normalize_s12_count(
    raw_value: object, *, existence_code: str, duplicate_code: str
) -> NormalizedObservation:
    """Normalize S12 using official existence/duplicate codes before the value."""

    raw = _raw_text(raw_value)
    if existence_code not in {"1", "2", "3", "4"}:
        raise ValueError(f"Unknown S12 existence code: {existence_code!r}")
    if duplicate_code not in {"1", "2", "3"}:
        raise ValueError(f"Unknown S12 duplicate code: {duplicate_code!r}")
    if existence_code == "4" or duplicate_code == "3":
        return NormalizedObservation(raw, None, "station_absent")
    if existence_code == "3":
        return NormalizedObservation(raw, None, "not_public")
    if existence_code == "2":
        return NormalizedObservation(raw, None, "source_absent")
    if duplicate_code == "2":
        return NormalizedObservation(raw, None, "duplicate_on_other_record")
    return normalize_estat_count(raw)


def normalize_census_count(
    raw_value: object, *, suppression_processing_code: str
) -> NormalizedObservation:
    """Normalize 2020 Census mesh counts while preserving aggregation roles."""

    raw = _raw_text(raw_value)
    if suppression_processing_code not in {"0", "1", "2"}:
        raise ValueError(
            "Unknown Census suppression processing code: "
            f"{suppression_processing_code!r}"
        )
    if suppression_processing_code == "2":
        return NormalizedObservation(raw, None, "suppressed")
    parsed = normalize_estat_count(raw)
    if suppression_processing_code == "1":
        if parsed.status not in {"observed", "observed_zero"}:
            raise ValueError("Aggregation destination requires a published numeric value")
        return NormalizedObservation(raw, parsed.numeric_value, "aggregation_destination")
    return parsed
