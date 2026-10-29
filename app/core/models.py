"""Internal value objects shared by detectors and the scoring engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskTag = Literal["prompt_injection", "pii", "rag_injection"]
PIIKind = Literal["email", "phone"]


@dataclass(frozen=True)
class Finding:
    """A single, explainable detector finding.

    ``location`` is ``"prompt"`` for prompt findings or the context document
    id for RAG/PII findings.  ``count`` is used only by the PII detector to
    aggregate multiple occurrences of the same PII kind in one piece of text.
    """

    tag: RiskTag
    rule_id: str
    weight: int
    evidence: str
    location: str = "prompt"
    count: int = 1


@dataclass(frozen=True)
class PIIMatch:
    """A PII span.  The raw value is deliberately not retained."""

    kind: PIIKind
    start: int
    end: int
