"""End-to-end analysis pipeline."""

from __future__ import annotations

from app.core.models import Finding
from app.core.pii import detect_pii
from app.core.policy import decide
from app.core.prompt_injection import detect_prompt_injection
from app.core.rag_injection import detect_rag_injection
from app.core.sanitizer import sanitize_context_doc, sanitize_prompt
from app.core.scoring import score_findings
from app.schemas import AnalyzeRequest, AnalyzeResponse, ContextDoc, Reason

_TAG_ORDER = {"prompt_injection": 0, "pii": 1, "rag_injection": 2}


def _risk_tags(findings: list[Finding]) -> list[str]:
    present = {finding.tag for finding in findings}
    return [tag for tag in ("prompt_injection", "pii", "rag_injection") if tag in present]


def _reasons(findings: list[Finding]) -> list[Reason]:
    ordered = sorted(findings, key=lambda finding: _TAG_ORDER[finding.tag])
    reasons: list[Reason] = []
    seen: set[tuple[str, str]] = set()
    for finding in ordered:
        key = (finding.tag, finding.evidence)
        if key in seen:
            continue
        seen.add(key)
        reasons.append(Reason(tag=finding.tag, evidence=finding.evidence))
    return reasons


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a validated request and return the policy response.

    The prompt and each retrieved document are analyzed independently, then
    their findings are combined by the scoring engine.  Sanitization is always
    applied so PII cannot leak through a ``block`` response either.
    """

    findings: list[Finding] = []
    findings.extend(detect_prompt_injection(request.prompt))
    findings.extend(detect_pii(request.prompt, "prompt"))

    for document in request.context_docs:
        findings.extend(detect_rag_injection(document.text, document.id))
        findings.extend(detect_pii(document.text, document.id))

    risk_score = score_findings(findings)
    decision = decide(risk_score)

    sanitized_docs = [
        ContextDoc(
            id=document.id,
            text=sanitize_context_doc(document.text, document.id),
        )
        for document in request.context_docs
    ]

    return AnalyzeResponse(
        decision=decision,
        risk_score=risk_score,
        risk_tags=_risk_tags(findings),
        sanitized_prompt=sanitize_prompt(request.prompt),
        sanitized_context_docs=sanitized_docs,
        reasons=_reasons(findings),
    )
