"""Locale registry — single source of truth for supported languages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Locale:
    code: str  # BCP-47-ish short code
    name: str  # English name
    formality_default: str  # formal | neutral | casual


SUPPORTED_LOCALES: dict[str, Locale] = {
    "en": Locale("en", "English", "neutral"),
    "tr": Locale("tr", "Turkish", "neutral"),
    "no": Locale("no", "Norwegian", "neutral"),
    "sv": Locale("sv", "Swedish", "neutral"),
    "da": Locale("da", "Danish", "neutral"),
    "de": Locale("de", "German", "formal"),
    "ar": Locale("ar", "Arabic", "formal"),
    "es": Locale("es", "Spanish", "neutral"),
    "fr": Locale("fr", "French", "formal"),
}


def is_supported(code: str) -> bool:
    return code in SUPPORTED_LOCALES


def list_locale_codes() -> list[str]:
    return list(SUPPORTED_LOCALES.keys())