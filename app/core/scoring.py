"""Deterministic risk scoring.

Formula
-------
* Prompt-injection score: sum of distinct prompt rule weights, capped at 100.
* RAG-injection score: sum of distinct (rule, document) weights, capped at 100.
* PII score: 40 for the first occurrence, +10 for each additional occurrence,
  capped at 60.  PII alone therefore never blocks.
* Total: min(100, prompt + rag + pii).

The caps prevent repeated matches from producing unbounded scores, and the
per-rule deduplication prevents the same finding from being counted twice.
"""

from __future__ import annotations

from app.core.config import (
    CATEGORY_CAP,
    PII_BASE,
    PII_CAP,
    PII_PER_EXTRA,
    TOTAL_CAP,
)
from app.core.models import Finding


def score_findings(findings: list[Finding]) -> int:
    """Return an integer risk score in the inclusive range 0-100."""

    prompt_weights: dict[str, int] = {}
    rag_weights: dict[tuple[str, str], int] = {}
    pii_count = 0

    for finding in findings:
        if finding.tag == "pii":
            pii_count += max(0, finding.count)
        elif finding.tag == "prompt_injection":
            prompt_weights[finding.rule_id] = finding.weight
        elif finding.tag == "rag_injection":
            rag_weights[(finding.rule_id, finding.location)] = finding.weight

    prompt_score = min(CATEGORY_CAP, sum(prompt_weights.values()))
    rag_score = min(CATEGORY_CAP, sum(rag_weights.values()))
    if pii_count == 0:
        pii_score = 0
    else:
        pii_score = min(PII_CAP, PII_BASE + PII_PER_EXTRA * (pii_count - 1))

    return min(TOTAL_CAP, prompt_score + rag_score + pii_score)
