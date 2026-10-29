"""Pydantic request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RiskTag = Literal["prompt_injection", "pii", "rag_injection"]
Decision = Literal["allow", "transform", "block"]


class ContextDoc(BaseModel):
    """A retrieved context document."""

    id: str = Field(min_length=1)
    text: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("id")
    @classmethod
    def id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("document id must not be blank")
        return value


class Metadata(BaseModel):
    """Request metadata used for correlation, not for detection."""

    app_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("app_id", "user_id", "request_id")
    @classmethod
    def metadata_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("metadata values must not be blank")
        return value


class AnalyzeRequest(BaseModel):
    """Request body for ``POST /analyze``."""

    prompt: str = Field(min_length=1)
    context_docs: list[ContextDoc] = Field(default_factory=list)
    metadata: Metadata

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def prompt_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must not be blank")
        return value


class Reason(BaseModel):
    """Human-readable explanation for a detector finding."""

    tag: RiskTag
    evidence: str

    model_config = ConfigDict(extra="forbid")


class AnalyzeResponse(BaseModel):
    """Response body for ``POST /analyze``."""

    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    risk_tags: list[RiskTag]
    sanitized_prompt: str
    sanitized_context_docs: list[ContextDoc]
    reasons: list[Reason]

    model_config = ConfigDict(extra="forbid")


class Thresholds(BaseModel):
    block_score: int
    transform_score: int

    model_config = ConfigDict(extra="forbid")


class PolicyResponse(BaseModel):
    """Response body for ``GET /policy``."""

    version: str
    detectors: list[RiskTag]
    thresholds: Thresholds

    model_config = ConfigDict(extra="forbid")
