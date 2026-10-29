"""Central configuration for SentraGuard Lite.

The policy version and thresholds are mandated by the assignment.  Detector
weights are intentionally defined here (rather than scattered across modules)
so the scoring model can be reviewed and explained in one place.

Threshold semantics
-------------------
* ``risk_score >= BLOCK_SCORE``      -> ``block``
* ``risk_score >= TRANSFORM_SCORE``  -> ``transform``
* otherwise                          -> ``allow``
"""

from __future__ import annotations

from typing import Final

POLICY_VERSION: Final[str] = "1"
DETECTOR_NAMES: Final[tuple[str, ...]] = (
    "prompt_injection",
    "pii",
    "rag_injection",
)

# Mandated policy thresholds.  Do not change these to make a test pass.
TRANSFORM_SCORE: Final[int] = 40
BLOCK_SCORE: Final[int] = 80

# --- Detector weights -------------------------------------------------------
# Prompt-injection and RAG-injection findings are additive within a category,
# then capped.  A single critical finding (80) blocks on its own; high and
# medium findings transform on their own but can combine to block.
PROMPT_CRITICAL: Final[int] = 80
PROMPT_HIGH: Final[int] = 55
PROMPT_MEDIUM: Final[int] = 40

RAG_CRITICAL: Final[int] = 80
RAG_HIGH: Final[int] = 55

# PII is sensitive but normally should be redacted rather than blocked.  The
# first occurrence contributes 40 (the transform threshold); each additional
# occurrence adds 10, capped at 60 so PII alone can never reach the block
# threshold.
PII_BASE: Final[int] = 40
PII_PER_EXTRA: Final[int] = 10
PII_CAP: Final[int] = 60

CATEGORY_CAP: Final[int] = 100
TOTAL_CAP: Final[int] = 100
