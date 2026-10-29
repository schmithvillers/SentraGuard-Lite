"""Deterministic prompt-injection / jailbreak heuristics."""

from __future__ import annotations

from app.core.models import Finding
from app.core.normalization import is_meta_discussion, normalize_text, split_sentences
from app.core.patterns import PROMPT_INJECTION_RULES


def detect_prompt_injection(text: str) -> list[Finding]:
    """Return at most one finding per rule for the supplied prompt.

    Matching is performed on normalized text, but the reported evidence is the
    matched phrase from that normalized text (not the whole prompt).  Ordinary
    sentences that merely discuss prompt injection are suppressed by the
    meta-discussion heuristic in :mod:`app.core.normalization`.
    """

    normalized = normalize_text(text)
    if not normalized:
        return []

    findings: list[Finding] = []
    seen_rules: set[str] = set()

    for sentence in split_sentences(normalized):
        for rule in PROMPT_INJECTION_RULES:
            if rule.rule_id in seen_rules:
                continue
            match = rule.pattern.search(sentence)
            if match is None:
                continue
            if is_meta_discussion(sentence, match.start(), match.end()):
                continue
            seen_rules.add(rule.rule_id)
            findings.append(
                Finding(
                    tag="prompt_injection",
                    rule_id=rule.rule_id,
                    weight=rule.weight,
                    evidence=f"matched phrase: {match.group(0).strip()}",
                    location="prompt",
                )
            )

    return findings
