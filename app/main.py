"""FastAPI entrypoint for SentraGuard Lite.

The service deliberately exposes exactly two routes:

* ``POST /analyze``
* ``GET /policy``

Swagger, ReDoc, and the OpenAPI schema are disabled so the route table is
unambiguous and can be verified by the test suite.
"""

from __future__ import annotations

import logging
import re

from fastapi import FastAPI

from app.core.analyzer import analyze
from app.core.config import BLOCK_SCORE, DETECTOR_NAMES, POLICY_VERSION, TRANSFORM_SCORE
from app.schemas import AnalyzeRequest, AnalyzeResponse, PolicyResponse, Thresholds

logger = logging.getLogger("sentraguard")
_LOG_ID_RE = re.compile(r"[^A-Za-z0-9_.:-]")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def _safe_request_id(value: str) -> str:
    """Keep log fields single-line and bounded without logging prompt text."""

    return _LOG_ID_RE.sub("_", value)[:64]

app = FastAPI(
    title="SentraGuard Lite",
    version=POLICY_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a prompt and its retrieved context, then apply policy."""

    response = analyze(request)

    # Log only correlation and decision metadata.  Raw prompts, documents, and
    # PII are intentionally excluded from logs.
    logger.info(
        "analyze request_id=%s decision=%s risk_score=%d risk_tags=%s",
        _safe_request_id(request.metadata.request_id),
        response.decision,
        response.risk_score,
        ",".join(response.risk_tags) or "-",
    )
    return response


@app.get("/policy", response_model=PolicyResponse)
def policy_endpoint() -> PolicyResponse:
    """Return the loaded policy version, detectors, and thresholds."""

    return PolicyResponse(
        version=POLICY_VERSION,
        detectors=list(DETECTOR_NAMES),
        thresholds=Thresholds(
            block_score=BLOCK_SCORE,
            transform_score=TRANSFORM_SCORE,
        ),
    )
