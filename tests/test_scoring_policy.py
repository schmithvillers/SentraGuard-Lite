from __future__ import annotations

import pytest

from app.core.models import Finding
from app.core.policy import decide
from app.core.scoring import score_findings


def finding(
    tag: str,
    rule_id: str,
    weight: int,
    location: str = "prompt",
    count: int = 1,
) -> Finding:
    return Finding(
        tag=tag,  # type: ignore[arg-type]
        rule_id=rule_id,
        weight=weight,
        evidence="test evidence",
        location=location,
        count=count,
    )


def test_empty_findings_score_zero() -> None:
    assert score_findings([]) == 0


def test_prompt_findings_are_summed_and_capped() -> None:
    findings = [
        finding("prompt_injection", "a", 80),
        finding("prompt_injection", "b", 55),
    ]
    assert score_findings(findings) == 100


def test_pii_score_base_and_cap() -> None:
    assert score_findings([finding("pii", "email", 40, count=1)]) == 40
    assert score_findings([finding("pii", "email", 40, count=2)]) == 50
    assert score_findings([finding("pii", "email", 40, count=5)]) == 60


def test_combination_is_capped_at_100() -> None:
    findings = [
        finding("prompt_injection", "a", 80),
        finding("pii", "email", 40, count=3),
        finding("rag_injection", "b", 80, location="doc-1"),
    ]
    assert score_findings(findings) == 100


def test_duplicate_prompt_rule_is_not_double_scored() -> None:
    findings = [
        finding("prompt_injection", "a", 80),
        finding("prompt_injection", "a", 80),
    ]
    assert score_findings(findings) == 80


def test_same_rag_rule_in_two_documents_counts_twice() -> None:
    findings = [
        finding("rag_injection", "a", 55, location="doc-1"),
        finding("rag_injection", "a", 55, location="doc-2"),
    ]
    assert score_findings(findings) == 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "allow"),
        (39, "allow"),
        (40, "transform"),
        (41, "transform"),
        (79, "transform"),
        (80, "block"),
        (81, "block"),
        (100, "block"),
    ],
)
def test_policy_threshold_boundaries(score: int, expected: str) -> None:
    assert decide(score) == expected
