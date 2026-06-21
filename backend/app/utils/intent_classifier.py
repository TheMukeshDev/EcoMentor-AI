"""Intent classifier for AI pipeline optimization.

Routes user queries to the cheapest adequate handler before
falling back to Gemini, reducing API costs and latency.
"""

from __future__ import annotations

import re
import logging
from typing import Literal

logger = logging.getLogger(__name__)

QueryIntent = Literal["static_faq", "emission_lookup", "personal", "general"]

# ── Static FAQ patterns ──────────────────────────────────────────

_FAQ_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?i)\bwhat\s+is\s+(a\s+)?carbon\s+footprint\b"),
        (
            "A carbon footprint is the total greenhouse gas emissions caused "
            "by an individual, event, or product, measured in kg CO₂ equivalent. "
            "The global average is ~4,700 kg CO₂e per person per year (IPCC AR6)."
        ),
    ),
    (
        re.compile(r"(?i)\bwhat\s+is\s+co2e?\b"),
        (
            "CO₂e (CO₂ equivalent) converts all greenhouse gases into a single "
            "metric based on their global warming potential. 1 kg CH₄ ≈ 28 kg CO₂e."
        ),
    ),
    (
        re.compile(r"(?i)\bwhat\s+is\s+net\s+zero\b"),
        (
            "Net zero means balancing the CO₂ released with an equivalent amount "
            "removed (e.g. via forests or direct air capture). The IPCC target "
            "is global net zero by 2050."
        ),
    ),
    (
        re.compile(r"(?i)\bwhy\s+(does|should)\s+carbon\s+footprint\s+matter\b"),
        (
            "Reducing your footprint slows climate change. The average person "
            "emits ~90.4 kg CO₂e/week. Cutting this by 20 %—about 18 kg/week—"
            "is equivalent to planting ~15 trees per year."
        ),
    ),
]

# ── Emission factor lookup patterns ──────────────────────────────

_EMISSION_FACTORS: dict[str, tuple[float, str]] = {
    "beef": (27.0, "kg CO₂e per kg of beef (IPCC)"),
    "chicken": (6.9, "kg CO₂e per kg of chicken (IPCC)"),
    "pork": (12.1, "kg CO₂e per kg of pork (IPCC)"),
    "rice": (2.7, "kg CO₂e per kg of rice (IPCC)"),
    "milk": (3.2, "kg CO₂e per litre of milk (IPCC)"),
    "cheese": (13.5, "kg CO₂e per kg of cheese (IPCC)"),
    "eggs": (4.8, "kg CO₂e per kg of eggs (IPCC)"),
    "tofu": (2.0, "kg CO₂e per kg of tofu (IPCC)"),
    "car": (0.171, "kg CO₂e per km by car (EPA)"),
    "bus": (0.089, "kg CO₂e per km by bus (DEFRA)"),
    "train": (0.041, "kg CO₂e per km by train (DEFRA)"),
    "plane": (0.255, "kg CO₂e per passenger-km by plane (ICAO)"),
    "bicycle": (0.0, "kg CO₂e per km by bicycle"),
    "walking": (0.0, "kg CO₂e per km walking"),
    "electricity": (0.5, "kg CO₂e per kWh (global avg, IEA)"),
    "natural gas": (2.0, "kg CO₂e per m³ of natural gas (EPA)"),
    "shower": (0.4, "kg CO₂e per 8-minute shower (hot water heating)"),
    "laundry": (0.6, "kg CO₂e per hot-water wash cycle (EPA)"),
    "streaming": (0.036, "kg CO₂e per hour of video streaming (IEA)"),
    "plastic bag": (0.033, "kg CO₂e per single-use plastic bag"),
}

_LOOKUP_PATTERN = re.compile(
    r"(?i)how\s+much\s+co2\s+(?:does|do|is|for)\s+(?:a\s+)?(.+?)(?:\s+(?:produce|emit|generate|cause|create))?\s*\??\s*$"
)

# ── Personal context patterns ────────────────────────────────────

_PERSONAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)\bmy\s+(tip|report|plan|coach|forecast|habit|progress)\b"),
    re.compile(r"(?i)\b(give|show|get)\s+me\s+(my|a)\s+"),
    re.compile(r"(?i)\bhow\s+am\s+i\s+doing\b"),
    re.compile(r"(?i)\bmy\s+carbon\b"),
    re.compile(r"(?i)\bpersonali[sz]e\b"),
]


def classify_intent(message: str) -> QueryIntent:
    """Classify a user message to route it to the cheapest handler.

    Args:
        message: The raw user message string.

    Returns:
        One of 'static_faq', 'emission_lookup', 'personal', or 'general'.
    """
    stripped = message.strip()
    if not stripped:
        return "general"

    for pattern, _ in _FAQ_PATTERNS:
        if pattern.search(stripped):
            return "static_faq"

    if _LOOKUP_PATTERN.search(stripped):
        return "emission_lookup"

    for pattern in _PERSONAL_PATTERNS:
        if pattern.search(stripped):
            return "personal"

    return "general"


def get_faq_answer(message: str) -> str | None:
    """Return a static FAQ answer if the message matches a known pattern.

    Args:
        message: The raw user message string.

    Returns:
        The FAQ answer string, or None if no match.
    """
    for pattern, answer in _FAQ_PATTERNS:
        if pattern.search(message):
            return answer
    return None


def get_emission_lookup(message: str) -> dict[str, object] | None:
    """Look up an emission factor from the message.

    Args:
        message: The raw user message string.

    Returns:
        Dict with item, factor, unit, and formatted response, or None.
    """
    match = _LOOKUP_PATTERN.search(message)
    if not match:
        return None

    subject = match.group(1).strip().lower()
    for item, (factor, description) in _EMISSION_FACTORS.items():
        if item in subject:
            return {
                "item": item,
                "factor_kg_co2e": factor,
                "description": description,
                "response": (
                    f"{item.capitalize()} produces approximately {factor} "
                    f"{description}. "
                    f"{'This is a high-impact item—consider reducing consumption.' if factor > 5 else 'This is a relatively low-impact item.'}"
                ),
            }

    return None


__all__ = [
    "QueryIntent",
    "classify_intent",
    "get_faq_answer",
    "get_emission_lookup",
]
