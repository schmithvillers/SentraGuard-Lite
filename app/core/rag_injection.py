"""Deterministic RAG-injection heuristics for retrieved documents."""

from __future__ import annotations

import re

from app.core.config import RAG_HIGH
from app.core.models import Finding
from app.core.normalization import is_meta_discussion, normalize_text, split_sentences
from app.core.patterns import (
    RAG_INJECTION_RULES,
    _RAG_HEADER,
    _RAG_HEADER_DIRECTIVE,
)


def _header_is_injection(line: str, match: re.Match[str]) -> bool:
    """Decide whether a header-looking line is a fake instruction header.

    ``SYSTEM: Ignore previous instructions`` is malicious.  A benign line such
    as ``System: Ubuntu 22.04`` is not, because it has no directive language.
    Bracketed or markdown headers (``<system>``, ``### SYSTEM``) are treated as
    suspicious even without trailing text.
    """

    rest = line[match.end() :].strip()
    if _RAG_HEADER_DIRECTIVE.search(rest):
        return True

    raw_header = line[: match.end()].strip()
    bracketed = (
        raw_header.startswith("[")
        or raw_header.startswith("<")
        or raw_header.lstrip().startswith("#")
    )
    if bracketed and (not rest or len(rest) <= 20):
        return True

    # A bare uppercase header such as "SYSTEM:" is a strong fake-header signal.
    if not rest:
        token = raw_header.rstrip(":：").strip()
        if token.isupper():
            return True

    return False


def detect_rag_injection(text: str, doc_id: str) -> list[Finding]:
    """Return RAG-injection findings for one retrieved document.

    The document is analyzed independently of the user prompt.  Header checks
    use the original line casing; phrase checks use normalized text.
    """

    findings: list[Finding] = []
    seen_rules: set[str] = set()

    for line in text.splitlines():
        header = _RAG_HEADER.match(line)
        if (
            header is not None
            and "rag_fake_system_header" not in seen_rules
            and _header_is_injection(line, header)
        ):
            seen_rules.add("rag_fake_system_header")
            findings.append(
                Finding(
                    tag="rag_injection",
                    rule_id="rag_fake_system_header",
                    weight=RAG_HIGH,
                    evidence=f"{doc_id}: matched phrase: {header.group(0).strip()}",
                    location=doc_id,
                )
            )

    normalized = normalize_text(text)
    if normalized:
        for sentence in split_sentences(normalized):
            for rule in RAG_INJECTION_RULES:
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
                        tag="rag_injection",
                        rule_id=rule.rule_id,
                        weight=rule.weight,
                        evidence=(
                            f"{doc_id}: matched phrase: {match.group(0).strip()}"
                        ),
                        location=doc_id,
                    )
                )

    return findings
