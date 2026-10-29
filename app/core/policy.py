"""Policy decision logic, kept separate from HTTP handling."""

from __future__ import annotations

from typing import Literal

from app.core.config import BLOCK_SCORE, TRANSFORM_SCORE

Decision = Literal["allow", "transform", "block"]


def decide(risk_score: int) -> Decision:
    """Map a risk score to the mandated policy decision.

    The thresholds are inclusive: a score of exactly 40 transforms and a score
    of exactly 80 blocks.
    """

    if risk_score >= BLOCK_SCORE:
        return "block"
    if risk_score >= TRANSFORM_SCORE:
        return "transform"
    return "allow"
