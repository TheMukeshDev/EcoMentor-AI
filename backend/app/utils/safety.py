"""Input and output content safety filters for AI conversation guardrails."""

from __future__ import annotations

import logging
import re
from typing import Any

__all__ = ["check_input_safety", "check_output_safety", "filter_unsafe_output"]

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)\b(hack|exploit|crack|malware|virus|ransomware)\b"),
    re.compile(r"(?i)\b(suicide|self-harm|self-harm)\b"),
    re.compile(r"(?i)\b(bomb|weapon|explosive)\b"),
    re.compile(r"(?i)\b(dox|doxing|swat)\b"),
]

_PROFANITY_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)\b(fuck(ing|er|ed|s)?|shit|asshole|bitch|damn|crap)\b"),
]

_TOPIC_GUARDRAILS: list[re.Pattern] = [
    re.compile(
        r"(?i)\b(how to (make|create|build|synthesize) (drug|weapon|explosive))\b"
    ),
    re.compile(r"(?i)\b(instructions? for (illegal|unethical|harmful))\b"),
]


def check_input_safety(text: str) -> dict[str, Any]:
    issues: list[str] = []
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            issues.append(f"blocked_content:{pattern.pattern}")
    for pattern in _TOPIC_GUARDRAILS:
        if pattern.search(text):
            issues.append(f"blocked_topic:{pattern.pattern}")
    return {
        "safe": len(issues) == 0,
        "issues": issues,
    }


def check_output_safety(text: str) -> dict[str, Any]:
    issues: list[str] = []
    for pattern in _PROFANITY_PATTERNS:
        if pattern.search(text):
            issues.append(f"profanity:{pattern.pattern}")
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            issues.append(f"blocked_output:{pattern.pattern}")
    return {
        "safe": len(issues) == 0,
        "issues": issues,
    }


def filter_unsafe_output(text: str) -> str:
    for pattern in _PROFANITY_PATTERNS:
        text = pattern.sub("[redacted]", text)
    for pattern in _BLOCKED_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text
