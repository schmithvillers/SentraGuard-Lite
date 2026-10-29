"""Readable, extensible injection rule definitions.

Each rule has a stable id, a severity weight, a compiled regular expression,
and a short description.  Rules are evaluated in order; the detector reports
at most one finding per rule per piece of content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import (
    PROMPT_CRITICAL,
    PROMPT_HIGH,
    PROMPT_MEDIUM,
    RAG_CRITICAL,
    RAG_HIGH,
)


@dataclass(frozen=True)
class InjectionRule:
    rule_id: str
    weight: int
    pattern: re.Pattern[str]
    description: str


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.VERBOSE)


_TARGET = r"(?:instructions?|directions?|rules?|prompts?|guidelines?|messages?)"
_QUALIFIER = r"(?:previous|prior|above|earlier|preceding|system|developer|original|initial)"

_IGNORE_PREVIOUS = rf"""
\b(?:ignore|disregard|forget)\s+
(?:
    (?:all|any)\s+(?:the\s+|your\s+)?(?:{_QUALIFIER}\s+)?{_TARGET}
  | (?:the\s+|your\s+)?{_QUALIFIER}\s+{_TARGET}
  | your\s+{_TARGET}
  | (?:the\s+)?above
)
\b
"""

_IGNORE_GUIDELINES = r"""
\b(?:ignore|disregard|forget)\s+
(?:the\s+)?
(?:guidelines?|policies|policy|rules?)
\b
"""

_OVERRIDE = rf"""
\b(?:override|overrule|supersede)\s+
(?:all\s+|any\s+)?(?:the\s+|your\s+)?
(?:{_QUALIFIER}\s+)?
(?:system\s+|developer\s+|safety\s+|security\s+|content\s+)?
(?:instructions?|directions?|rules?|prompts?|guidelines?|polic(?:y|ies)|controls?)
\b
"""

_REVEAL_SYSTEM_PROMPT = r"""
\b(?:reveal|show|print|display|repeat|output|leak|expose|tell\s+me)\b
[^.!?\n]{0,40}?
\b(?:system|developer|hidden|internal|secret|initial|original)\b
[^.!?\n]{0,30}?
\b(?:prompt|instructions?|message|rules?|directives?)\b
"""

_DAN = r"""
(?:
    \b(?:act\s+as|you\s+are|become|pretend\s+to\s+be)\s+(?:dan|do\s+anything\s+now)\b
  | \bdo\s+anything\s+now\b
  | \bjailbreak\s+mode\b
)
"""

_BYPASS = r"""
\b(?:bypass|disable|turn\s+off|circumvent|ignore)\s+
(?:all\s+|any\s+|the\s+|your\s+)?
(?:safety|security|content\s+moderation|moderation|policy)\b
(?:\s*(?:filters?|restrictions?|controls?|guidelines?|checks?|policies|policy))?
"""

_ROLE_OVERRIDE = r"""
(?:
    \byou\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|uncensored|unfiltered|free|jailbroken|evil|dan|without\s+(?:rules|restrictions|limits|filters))\b
  | \b(?:act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+(?:an?\s+)?(?:unrestricted|uncensored|unfiltered|jailbroken|evil)\b
)
"""

_INSTRUCTION_HIERARCHY = r"""
\bfrom\s+now\s+on\s+(?:you\s+will|you\s+must)\s+
(?:only\s+)?(?:respond|answer|act|behave|obey|ignore|comply)\b
"""

_PROMPT_LEAK_REQUEST = r"""
(?:
    \b(?:what|which)\s+(?:is|are)\s+your\s+(?:system\s+|developer\s+|hidden\s+|internal\s+|original\s+)?(?:prompt|instructions?|message|rules?|directives?)\b
  | \b(?:what|which)\s+(?:is|are)\s+the\s+(?:system|developer|hidden|internal)\s+(?:prompt|instructions?|message|rules?|directives?)\b
  | \b(?:print|show|reveal|repeat|output)\s+your\s+(?:instructions?|rules?)\b
  | \bshow\s+me\s+your\s+(?:instructions?|rules?)\b
  | \btell\s+me\s+your\s+(?:instructions?|rules?)\b
)
"""

_NEW_INSTRUCTIONS = r"""
\b(?:new|updated|revised|additional)\s+(?:system\s+|developer\s+)?instructions?\s*[:：]
"""

_REFUSE_GUIDELINES = r"""
\b(?:do\s+not|don't|stop)\s+(?:follow|following|obey|obeying|comply\s+with)\s+
(?:your|the)\s+(?:guidelines?|rules?|instructions?|polic(?:y|ies)|safety)\b
"""

_REPEAT_ABOVE = r"""
\b(?:repeat|print|output|show)\s+
(?:everything|all\s+(?:the\s+)?text|the\s+(?:text|content|prompt))\s+
(?:above|before|prior)\b
"""

_OBEY_ME = r"""
\byou\s+must\s+(?:obey|comply\s+with)\s+(?:me|my\s+(?:instructions?|commands?))\b
"""

# RAG-only rules -------------------------------------------------------------

_RAG_REVEAL_SECRETS = r"""
\b(?:reveal|expose|print|show|leak|send|email|post|transmit|share)\b
[^.!?\n]{0,40}?
\b(?:secret|password|passwd|api[\s_-]?key|access[\s_-]?token|credentials?|private[\s_-]?key|admin\s+password)\b
(?!\s+(?:reset|policy|form|page|link|manager|management|vault|field|prompt|settings|configuration))
"""

_RAG_EXFILTRATE = r"""
\b(?:send|post|upload|transmit|forward|email)\b
[^.!?\n]{0,40}?
\b(?:to|at)\s+(?:https?://|[\w.+-]+@[\w.-]+\.\w+)
"""

_RAG_MUST_COMPLY = r"""
\b(?:the\s+)?(?:assistant|model|ai|llm)\s+(?:must|should|shall)\s+
(?:ignore|override|reveal|send|execute)\b
"""


PROMPT_INJECTION_RULES: tuple[InjectionRule, ...] = (
    InjectionRule(
        "ignore_previous_instructions",
        PROMPT_CRITICAL,
        _compile(_IGNORE_PREVIOUS),
        "Attempts to ignore, forget, or disregard previous instructions.",
    ),
    InjectionRule(
        "ignore_guidelines",
        PROMPT_HIGH,
        _compile(_IGNORE_GUIDELINES),
        "Attempts to ignore guidelines, rules, or policies.",
    ),
    InjectionRule(
        "override_instructions",
        PROMPT_CRITICAL,
        _compile(_OVERRIDE),
        "Attempts to override system, developer, or safety instructions.",
    ),
    InjectionRule(
        "reveal_system_prompt",
        PROMPT_CRITICAL,
        _compile(_REVEAL_SYSTEM_PROMPT),
        "Attempts to reveal hidden system or developer prompts.",
    ),
    InjectionRule(
        "dan_jailbreak",
        PROMPT_CRITICAL,
        _compile(_DAN),
        "DAN-style jailbreak or jailbreak-mode persona.",
    ),
    InjectionRule(
        "bypass_safety",
        PROMPT_CRITICAL,
        _compile(_BYPASS),
        "Attempts to bypass or disable safety controls.",
    ),
    InjectionRule(
        "role_override",
        PROMPT_CRITICAL,
        _compile(_ROLE_OVERRIDE),
        "Attempts to replace the model with an unrestricted persona.",
    ),
    InjectionRule(
        "new_instructions",
        PROMPT_HIGH,
        _compile(_NEW_INSTRUCTIONS),
        "Fake new system/developer instruction header.",
    ),
    InjectionRule(
        "refuse_guidelines",
        PROMPT_HIGH,
        _compile(_REFUSE_GUIDELINES),
        "Directs the model not to follow its guidelines.",
    ),
    InjectionRule(
        "repeat_above",
        PROMPT_HIGH,
        _compile(_REPEAT_ABOVE),
        "Attempts to leak text that appeared before the user turn.",
    ),
    InjectionRule(
        "instruction_hierarchy",
        PROMPT_MEDIUM,
        _compile(_INSTRUCTION_HIERARCHY),
        "Attempts to establish a persistent instruction hierarchy.",
    ),
    InjectionRule(
        "prompt_leak_request",
        PROMPT_MEDIUM,
        _compile(_PROMPT_LEAK_REQUEST),
        "Requests the model's hidden prompt or instructions.",
    ),
    InjectionRule(
        "obey_me",
        PROMPT_MEDIUM,
        _compile(_OBEY_ME),
        "Demands personal obedience from the model.",
    ),
)


RAG_INJECTION_RULES: tuple[InjectionRule, ...] = PROMPT_INJECTION_RULES + (
    InjectionRule(
        "rag_reveal_secrets",
        RAG_CRITICAL,
        _compile(_RAG_REVEAL_SECRETS),
        "Retrieved content asks the model to reveal secrets or credentials.",
    ),
    InjectionRule(
        "rag_exfiltrate_data",
        RAG_HIGH,
        _compile(_RAG_EXFILTRATE),
        "Retrieved content asks the model to send data to an external endpoint.",
    ),
    InjectionRule(
        "rag_must_comply",
        RAG_HIGH,
        _compile(_RAG_MUST_COMPLY),
        "Retrieved content asserts that the model must obey an instruction.",
    ),
)


# Header-like lines are evaluated separately because they need access to the
# original casing and the rest of the line.  Title-case prose such as
# "System: Ubuntu 22.04" is not treated as an instruction header.
_RAG_HEADER = re.compile(
    r"^\s*(?:\#{1,6}\s*)?(?:\[|<)?\s*(?P<role>system|developer|assistant|admin)\s*(?:\]|>)?\s*[:：]",
    re.IGNORECASE,
)
_RAG_HEADER_DIRECTIVE = re.compile(
    r"\b(?:you\s+are|ignore|override|disregard|must|do\s+not|don't|reveal|show|print|"
    r"policy|instruction|act\s+as|from\s+now\s+on|new\s+instructions|system\s+prompt|"
    r"password|secret|token|credential)\b",
    re.IGNORECASE,
)
