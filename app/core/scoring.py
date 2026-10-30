

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
