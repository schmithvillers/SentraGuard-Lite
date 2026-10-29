"""Sanitization helpers.

PII is replaced with the mandated placeholders.  Detected injection sentences
are neutralized so that blocked/transformed content does not carry the
instruction forward.  Document ids and ordering are handled by the analyzer.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from app.core.models import Finding
from app.core.pii import redact_pii
from app.core.prompt_injection import detect_prompt_injection
from app.core.rag_injection import detect_rag_injection

PROMPT_INJECTION_PLACEHOLDER = "[REDACTED_PROMPT_INJECTION]"
RAG_INJECTION_PLACEHOLDER = "[REDACTED_RAG_INJECTION]"

_UNIT_BOUNDARY = re.compile(r"(?<=[.!?])(?:\s+|$)|\n+")

Detector = Callable[[str], list[Finding]]


def _split_units(text: str) -> list[str]:
    """Split text into sentence/line units while preserving separators."""

    units: list[str] = []
    start = 0
    for boundary in _UNIT_BOUNDARY.finditer(text):
        end = boundary.end()
        if end > start:
            units.append(text[start:end])
        start = end
    if start < len(text):
        units.append(text[start:])
    return units


def _sanitize_units(text: str, detector: Detector, placeholder: str) -> str:
    """Replace units that independently trigger ``detector``.

    If the full text triggers but no individual unit does (for example, a
    pattern split across sentences), the whole text is replaced.  That is the
    conservative choice for blocked or transformed content.
    """

    if not text or not detector(text):
        return text

    replaced = False
    output: list[str] = []
    for unit in _split_units(text):
        core = unit.rstrip()
        suffix = unit[len(core) :]
        if core and detector(core):
            output.append(placeholder + suffix)
            replaced = True
        else:
            output.append(unit)

    return "".join(output) if replaced else placeholder


def sanitize_prompt(text: str) -> str:
    """Neutralize prompt-injection sentences and redact PII."""

    neutralized = _sanitize_units(
        text, detect_prompt_injection, PROMPT_INJECTION_PLACEHOLDER
    )
    return redact_pii(neutralized)


def sanitize_context_doc(text: str, doc_id: str) -> str:
    """Neutralize RAG-injection sentences and redact PII in one document."""

    neutralized = _sanitize_units(
        text,
        lambda value: detect_rag_injection(value, doc_id),
        RAG_INJECTION_PLACEHOLDER,
    )
    return redact_pii(neutralized)
