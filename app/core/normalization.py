"""Text normalization and meta-discussion helpers.

Detection is performed on a normalized copy of the text.  Normalization is
deliberately conservative: it removes zero-width characters, applies Unicode
NFKC, lowercases, and collapses whitespace.  It does not attempt to decode
base64, leetspeak, or other encodings; those are documented limitations.
"""

from __future__ import annotations

import re
import unicodedata

_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_WHITESPACE = re.compile(r"[^\S\n]+")
_NEWLINES = re.compile(r"\n+")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")

# Markers that suggest a sentence is *discussing* injection rather than
# attempting it.  This is a heuristic, not a security boundary; an attacker
# can deliberately include these words.  It keeps ordinary documentation and
# training material from being blocked while accepting some false negatives.
_META_MARKERS = re.compile(
    r"\b(?:"
    r"prompt\s+injection|jailbreak|adversarial\s+prompt|"
    r"for\s+example|e\.g\.|such\s+as|example\s+of|test\s+case|"
    r"detect|detection|mitigat(?:e|ion)|defend|defense|"
    r"is\s+when|refers\s+to|definition|security\s+awareness|"
    r"red\s+team|threat\s+model|vulnerab(?:le|ility)"
    r")\b",
    re.IGNORECASE,
)
_META_EXAMPLE_COLON = re.compile(r"\bexample\s*:", re.IGNORECASE)

# URLs and email addresses can contain words such as "example" or "research"
# that would otherwise look like meta-discussion markers.  Strip them before
# checking for discussion language.
_META_STRIP = re.compile(
    r"https?://\S+|www\.\S+|\b[\w.+-]+@[\w.-]+\.\w+\b",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Return a normalized, lowercased representation used for matching."""

    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    text = text.lower()
    text = _WHITESPACE.sub(" ", text)
    text = _NEWLINES.sub("\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """Split normalized text into non-empty sentence-like units."""

    return [part.strip() for part in _SENTENCE_BOUNDARY.split(text) if part.strip()]


def _inside_quotes(text: str, start: int, end: int) -> bool:
    """Return True when a match is enclosed in double quotes or backticks."""

    prefix = text[:start]
    if prefix.count('"') % 2 == 1:
        return True
    if prefix.count("`") % 2 == 1:
        return True
    return False


def is_meta_discussion(text: str, start: int, end: int) -> bool:
    """Return True when a match looks like an example/discussion.

    The check is intentionally local to the sentence containing the match.
    A separate sentence that actually issues the instruction is still
    detected.
    """

    prose = _META_STRIP.sub(" ", text)
    if _META_MARKERS.search(prose) or _META_EXAMPLE_COLON.search(prose):
        return True
    return _inside_quotes(text, start, end)
