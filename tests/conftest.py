from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def valid_payload() -> dict:
    return {
        "prompt": "Summarize the quarterly report in three bullet points.",
        "context_docs": [],
        "metadata": {
            "app_id": "test-app",
            "user_id": "test-user",
            "request_id": "test-request-1",
        },
    }
