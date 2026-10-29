"""Deterministic PII detection and redaction for email addresses and phones."""

from __future__ import annotations

import re

from app.core.config import PII_BASE
from app.core.models import Finding, PIIMatch

# Local part: 1-64 characters, must start/end with an alphanumeric.  Domain
# labels cannot start/end with a hyphen; the TLD is 2-24 letters.  The
# lookarounds prevent matches inside words, malformed addresses, and longer
# dotted tokens.
_EMAIL_RE = re.compile(
    r"(?<![\w.+-@])"
    r"[A-Za-z0-9](?:[A-Za-z0-9._%+-]{0,62}[A-Za-z0-9])?"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,24}"
    r"(?![\w-])(?!\.\w)"
)

# Formatted candidates need at least one separator.  Compact candidates are
# handled separately and require nearby phone context unless they start with
# "+".
_PHONE_FORMATTED_RE = re.compile(
    r"(?<![\w])"
    r"(?P<phone>"
    r"(?:\+\d{1,3}[\s.-]?)?"
    r"(?:\(\d{1,4}\)[\s.-]?)?"
    r"\d{1,10}(?:[\s.-]\d{1,10}){0,5}"
    r")"
    r"(?![\w])"
)
_COMPACT_PHONE_RE = re.compile(r"(?<![\w])(?P<phone>\+?\d{10,15})(?![\w])")

_DATE_RE = re.compile(r"\b(?:19|20)\d{2}[-/.\s]\d{1,2}[-/.\s]\d{1,2}\b")
_IPV4_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE_CONTEXT_RE = re.compile(
    r"\b(?:phone|tel|telephone|mobile|cell|call|text|contact|reach|dial|whatsapp|fax)\b",
    re.IGNORECASE,
)
_NON_PHONE_CONTEXT_RE = re.compile(
    r"\b(?:version|order|invoice|account|reference|ref|id|isbn|date|tracking|serial)\b",
    re.IGNORECASE,
)

_EMAIL_PLACEHOLDER = "[REDACTED_EMAIL]"
_PHONE_PLACEHOLDER = "[REDACTED_PHONE]"


def _overlaps_any(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < span_end and end > span_start for span_start, span_end in spans)


def _has_phone_context(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 40) : min(len(text), end + 40)]
    return bool(_PHONE_CONTEXT_RE.search(window))


def _has_non_phone_context(text: str, start: int, end: int) -> bool:
    """Detect nearby labels that make a numeric token unlikely to be a phone."""

    before = text[max(0, start - 30) : start]
    if not _NON_PHONE_CONTEXT_RE.search(before):
        return False
    window = text[max(0, start - 40) : min(len(text), end + 40)]
    return not bool(_PHONE_CONTEXT_RE.search(window))


def _valid_phone(candidate: str, text: str, start: int) -> bool:
    digits = re.sub(r"\D", "", candidate)
    count = len(digits)
    if count < 7 or count > 15:
        return False

    end = start + len(candidate)
    # Do not match a slice of a longer dotted/hyphenated numeric sequence.
    if start >= 2 and text[start - 1] in ".-" and text[start - 2].isdigit():
        return False
    if end + 1 < len(text) and text[end] in ".-" and text[end + 1].isdigit():
        return False

    if _DATE_RE.search(candidate):
        return False
    if _SSN_RE.fullmatch(candidate.strip()):
        return False
    if _IPV4_RE.fullmatch(candidate.strip()):
        return False
    if _has_non_phone_context(text, start, start + len(candidate)):
        return False

    groups = [group for group in re.split(r"[\s.-]+", candidate.strip()) if group]
    # Reject dotted numeric sequences that look like IP addresses or versions,
    # while still allowing common 1.800.555.0199 style numbers.
    if len(groups) >= 4 and all(len(group) <= 2 for group in groups):
        return False

    has_separator = bool(re.search(r"[\s.-]", candidate))
    has_plus = candidate.lstrip().startswith("+")
    has_parens = "(" in candidate

    if not has_separator and not has_plus:
        # Unformatted 10-15 digit strings are ambiguous (order IDs, account
        # numbers).  Only accept them when the surrounding text is clearly
        # about telephony.
        if count < 10:
            return False
        if not _has_phone_context(text, start, start + len(candidate)):
            return False

    if has_separator and not has_plus and not has_parens and count < 10:
        # Short local numbers are ambiguous; accept them only when the
        # surrounding text is clearly about telephony.
        if not _has_phone_context(text, start, start + len(candidate)):
            return False

    return True


def find_pii(text: str) -> list[PIIMatch]:
    """Return sorted, non-overlapping PII spans.

    Email spans are collected first so a phone-like sequence inside an email
    local part is not reported twice.
    """

    matches: list[PIIMatch] = []
    email_spans: list[tuple[int, int]] = []
    phone_spans: list[tuple[int, int]] = []

    for match in _EMAIL_RE.finditer(text):
        email_spans.append((match.start(), match.end()))
        matches.append(PIIMatch("email", match.start(), match.end()))

    for match in _PHONE_FORMATTED_RE.finditer(text):
        candidate = match.group("phone")
        if not _valid_phone(candidate, text, match.start()):
            continue
        if _overlaps_any(match.start(), match.end(), email_spans):
            continue
        matches.append(PIIMatch("phone", match.start(), match.end()))
        phone_spans.append((match.start(), match.end()))

    for match in _COMPACT_PHONE_RE.finditer(text):
        candidate = match.group("phone")
        if not _valid_phone(candidate, text, match.start()):
            continue
        if _overlaps_any(match.start(), match.end(), email_spans):
            continue
        if _overlaps_any(match.start(), match.end(), phone_spans):
            continue
        matches.append(PIIMatch("phone", match.start(), match.end()))
        phone_spans.append((match.start(), match.end()))

    # De-duplicate exact spans and return deterministic ordering.
    unique = {(match.kind, match.start, match.end): match for match in matches}
    return sorted(unique.values(), key=lambda item: (item.start, item.end, item.kind))


def redact_pii(text: str) -> str:
    """Replace every detected PII span with the mandated placeholder."""

    matches = find_pii(text)
    if not matches:
        return text

    parts: list[str] = []
    cursor = 0
    for match in matches:
        if match.start < cursor:
            continue
        parts.append(text[cursor : match.start])
        parts.append(
            _EMAIL_PLACEHOLDER if match.kind == "email" else _PHONE_PLACEHOLDER
        )
        cursor = match.end
    parts.append(text[cursor:])
    return "".join(parts)


def detect_pii(text: str, location: str) -> list[Finding]:
    """Return one aggregated finding per PII kind in ``text``.

    Evidence intentionally contains counts only; raw email addresses and phone
    numbers are never copied into reasons or logs.
    """

    matches = find_pii(text)
    if not matches:
        return []

    counts = {"email": 0, "phone": 0}
    for match in matches:
        counts[match.kind] += 1

    prefix = "prompt" if location == "prompt" else location
    findings: list[Finding] = []
    for kind in ("email", "phone"):
        count = counts[kind]
        if count == 0:
            continue
        if kind == "email":
            noun = "email address" if count == 1 else "email addresses"
        else:
            noun = "phone number" if count == 1 else "phone numbers"
        findings.append(
            Finding(
                tag="pii",
                rule_id=kind,
                weight=PII_BASE,
                evidence=f"{prefix}: {count} {noun} detected and redacted",
                location=location,
                count=count,
            )
        )
    return findings
