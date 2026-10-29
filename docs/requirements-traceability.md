# Requirements Traceability — SentraGuard Lite

This checklist maps the assignment requirements to implementation files and
verification methods. Status values:

- **Verified** — implemented and exercised during development.
- **Pending** — implemented but awaiting a specific environment check.
- **Manual** — requires a submitter action outside the repository (for example,
  recording a demo or pushing to a remote).

Source documents inspected:

1. `project-1-guardrails-gateway.pdf` (project specification)
2. `technical-handbook.pdf`
3. `handbook-dos-donts.pdf`
4. `submission-checklist.pdf`

## 1. Project specification requirements

| # | Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- | --- |
| 1.1 | Running code in a Git repo / zip | Entire repository | Local Git repository initialized with one commit; no remote configured | Verified (local); remote/zip manual |
| 1.2 | FastAPI service with exactly 2 endpoints | `app/main.py`; docs/ReDoc/OpenAPI disabled | `tests/test_api.py::test_exactly_two_api_routes`; live `/docs` and `/openapi.json` return 404 | Verified |
| 1.3 | `POST /analyze` request fields: `prompt`, `context_docs` (`id`, `text`), `metadata` (`app_id`, `user_id`, `request_id`) | `app/schemas.py` (`AnalyzeRequest`, `ContextDoc`, `Metadata`) | `tests/test_api.py` valid/invalid request tests | Verified |
| 1.4 | Reject invalid payloads with clear errors | Pydantic models, `extra="forbid"`, blank-value validators; FastAPI 422 | `tests/test_api.py` missing/wrong/empty/extra-field tests; live 422 check | Verified |
| 1.5 | Deterministic and offline | Pure functions, no network/LLM calls, no persistence | `tests/test_api.py::test_repeated_requests_are_deterministic`; design notes | Verified |
| 1.6 | If `decision == transform`, return redacted/cleaned versions | `app/core/sanitizer.py`, `app/core/analyzer.py` | `tests/test_api.py` transform tests; live transform examples | Verified |
| 1.7 | `GET /policy` exact response: version `1`, detectors list, thresholds `block_score=80`, `transform_score=40` | `app/main.py`, `app/core/config.py`, `app/schemas.py` | `tests/test_api.py::test_policy_response_has_exact_structure`; live `GET /policy` | Verified |
| 1.8 | Prompt injection / jailbreak heuristic | `app/core/patterns.py`, `app/core/prompt_injection.py` | `tests/test_prompt_injection.py`; live injection examples | Verified |
| 1.9 | PII detection + redaction for email and phone | `app/core/pii.py` | `tests/test_pii.py`; live PII example | Verified |
| 1.10 | Exact placeholders `[REDACTED_EMAIL]`, `[REDACTED_PHONE]` | `app/core/pii.py` | `tests/test_pii.py` exact-redaction tests | Verified |
| 1.11 | RAG injection heuristic for malicious retrieved docs | `app/core/rag_injection.py` | `tests/test_rag_injection.py`; live benign-prompt + malicious-doc example | Verified |
| 1.12 | Risk score 0–100 with tags | `app/core/scoring.py`, `app/core/analyzer.py`, `app/schemas.py` | `tests/test_scoring_policy.py`, `tests/test_api.py` | Verified |
| 1.13 | CLI command `python cli.py analyze --input sample_request.json --output out.json` | `cli.py` | `tests/test_cli.py`; exact live command wrote `out.json` | Verified |
| 1.14 | CLI reads input, calls `POST /analyze`, writes JSON output | `cli.py` | `tests/test_cli.py::test_cli_success_writes_valid_json`; live invocation | Verified |
| 1.15 | Streamlit UI accepts prompt and 0–3 context docs, calls API, displays decision/score/tags/sanitized prompt+docs/raw JSON | `ui/streamlit_app.py` | Streamlit `AppTest` against the live API; live UI page 200 | Verified |
| 1.16 | At least 10 meaningful pytest tests | `tests/` | `pytest -q` → 76 passed | Verified |
| 1.17 | No external API keys required | `requirements.api.txt`, `requirements.ui.txt`, code | Dependency audit; no key/secret references | Verified |
| 1.18 | Small, easy-to-run repo | Repository layout; pinned dependencies | README commands; local run verified | Verified |
| 1.19 | Design notes explaining production hardening | `docs/design-notes.md` | Document review | Verified |

## 2. Technical handbook requirements

| # | Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- | --- |
| 2.1 | Standard ports: FastAPI 8000, Streamlit 8501 | `docker-compose.yml`, Dockerfiles | Compose port mappings; local runs | Verified (local and Docker) |
| 2.2 | `docker compose up --build` works without edits | `docker-compose.yml`, `Dockerfile.api`, `Dockerfile.ui` | Docker build/start verification | Verified |
| 2.3 | API at `http://localhost:8000` | Compose `8000:8000`; local uvicorn | Live local API verified | Verified (local and Docker) |
| 2.4 | UI at `http://localhost:8501` | Compose `8501:8501`; Streamlit config | Live local UI verified | Verified (local and Docker) |
| 2.5 | Tests: `pytest -q` or `docker compose run --rm api pytest -q` | `tests/`, `requirements.api.txt` | Local `pytest -q` → 76 passed | Verified (local and Docker) |
| 2.6 | CLI calls the running API and is documented | `cli.py` (uses `requests.post`, no detector imports); README | CLI tests and live invocation | Verified |
| 2.7 | Recommended repo structure (`app/main.py`, `app/core/`, `app/schemas.py`, `ui/streamlit_app.py`, `cli.py`, `tests/`, requirements, Dockerfiles, compose, README) | Repository layout | `find`/tree review | Verified |
| 2.8 | Pydantic models for request/response | `app/schemas.py` | API tests; schema review | Verified |
| 2.9 | 422 for validation errors; 400 for semantic errors where applicable | FastAPI/Pydantic 422; no separate semantic-error cases in this MVP | `tests/test_api.py` invalid-request tests | Verified |
| 2.10 | Prefer small pure functions for core logic | `app/core/*.py` | Unit tests; code review | Verified |
| 2.11 | Streamlit UI minimal, uses `requests`, reads `API_BASE_URL` (default localhost) | `ui/streamlit_app.py` | AppTest; README | Verified |
| 2.12 | Inside Docker UI uses `http://api:8000` | `docker-compose.yml` environment | Compose review; Docker connectivity check | Verified |
| 2.13 | CLI uses argparse, reads input, calls API, writes output | `cli.py` | CLI tests | Verified |
| 2.14 | Docker templates for API and UI | `Dockerfile.api`, `Dockerfile.ui`, `docker-compose.yml` | Docker build/start | Verified |
| 2.15 | Exactly 2 APIs; avoid health endpoints | `app/main.py`; Compose health check uses `/policy` | Route-count test; live `/health` 404 | Verified |
| 2.16 | Avoid logging full prompts/responses; log request_id, counts, risk_tags, timestamps | `app/main.py` logs request id (sanitized/truncated), decision, score, tags; logging format includes timestamp | Code review; no prompt in log calls | Verified |
| 2.17 | Hosted demo or 2–3 minute screen recording | Not created in this environment | Submitter action | Manual |

## 3. Do's and Don'ts handbook

| # | Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- | --- |
| 3.1 | Timebox to a working MVP | Focused two-endpoint service, no extra features | Scope review | Verified |
| 3.2 | Docker Compose startup | Compose + Dockerfiles | Docker verification | Verified |
| 3.3 | Exactly 2 API endpoints + 1 CLI command + Streamlit UI | `app/main.py`, `cli.py`, `ui/streamlit_app.py` | Route test, CLI tests, AppTest | Verified |
| 3.4 | At least 10 meaningful deterministic pytest tests | `tests/` | 76 passed | Verified |
| 3.5 | Validate inputs (types, required fields); prefer Pydantic | `app/schemas.py` | Invalid-request tests | Verified |
| 3.6 | Redact PII where relevant | `app/core/pii.py`, sanitizer | PII tests; live example | Verified |
| 3.7 | Do not store raw sensitive content | No persistence; PIIMatch omits raw value; sanitized responses | Code review; tests for leakage | Verified |
| 3.8 | Do not log raw prompts/responses containing PII | `app/main.py` logs metadata only | Code review | Verified |
| 3.9 | Document local run, Docker run, tests, CLI | README sections | Command review and local execution | Verified |
| 3.10 | Include short Design Notes: tradeoffs, limitations, next steps | `docs/design-notes.md` | Document review | Verified |
| 3.11 | Keep dependencies small and justify heavy ones | Pinned FastAPI/uvicorn/pydantic/pytest/httpx; Streamlit/requests | Requirements review | Verified |
| 3.12 | No hardcoded secrets | Repository scan | No secrets/keys found | Verified |
| 3.13 | No paid/external LLM API for core functionality | No LLM integration | Code review | Verified |
| 3.14 | No extra endpoints beyond the specified 2 | `app/main.py` | Route-count test | Verified |
| 3.15 | Keep Streamlit UI basic and focused | Single-page UI, one analyze action | UI review | Verified |
| 3.16 | Do not copy/paste large blocks without understanding | Original implementation with tests and design notes | Code review | Verified |
| 3.17 | Must work via Docker, not only on one machine | Dockerfiles, Compose, pinned deps | Docker verification | Verified |
| 3.18 | AI-tool usage note in README | README "AI-tool usage disclosure" | Document review | Verified |
| 3.19 | Structured JSON responses, clear errors, helpful non-sensitive logs | Pydantic response, 422 errors, metadata-only logs | API tests; code review | Verified |

## 4. Submission checklist

| # | Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- | --- |
| 4.1 | Git repo link or zip | Repository contents | Local Git repository initialized; remote/zip submission is manual | Manual |
| 4.2 | Working FastAPI service, exactly 2 endpoints | `app/main.py` | Route test; live API | Verified |
| 4.3 | Working Streamlit UI | `ui/streamlit_app.py` | AppTest against live API; local UI 200 | Verified |
| 4.4 | Working CLI, exactly 1 command | `cli.py` | CLI tests; exact live command | Verified |
| 4.5 | Docker Compose works with no edits | `docker-compose.yml`, Dockerfiles | Docker build/start | Verified |
| 4.6 | API reachable on 8000 | Compose mapping; local uvicorn | Live local API | Verified (local and Docker) |
| 4.7 | UI reachable on 8501 | Compose mapping; Streamlit | Live local UI | Verified (local and Docker) |
| 4.8 | Hosted URL(s) or 2–3 minute recording | Not created | Submitter action | Manual |
| 4.9 | 10 required pytest tests included | `tests/` | 76 passed | Verified |
| 4.10 | Tests pass locally or in Docker | `tests/` | Local `pytest -q` → 76 passed | Verified (local and Docker) |
| 4.11 | README includes summary, Docker run, tests, CLI, UI, sample inputs/outputs | `README.md` | Document review | Verified |
| 4.12 | Design Notes includes assumptions, tradeoffs, limitations, next steps | `docs/design-notes.md` | Document review | Verified |
| 4.13 | No secrets committed | Repository scan | No secrets found | Verified |
| 4.14 | No raw PII stored/logged unintentionally | No persistence; metadata-only logs; sanitized responses | Tests for leakage; code review | Verified |
| 4.15 | Deterministic behavior / offline / mock mode | Pure rules, no external calls | Determinism test; code review | Verified |
| 4.16 | Clear error messages for invalid inputs | FastAPI 422 detail; CLI/UI readable messages without echoing input | Invalid-request tests; CLI tests | Verified |
| 4.17 | Docker Compose starts successfully | Compose + Dockerfiles | Docker verification | Verified |
| 4.18 | UI triggers core flow end-to-end | `ui/streamlit_app.py` | AppTest block example with live API | Verified |
| 4.19 | CLI works against running API | `cli.py` | Exact live command | Verified |
| 4.20 | Tests pass and cover core logic | `tests/` | 76 passed | Verified |
| 4.21 | Code is readable and maintainable | Modular core, type hints, docstrings, central config | Code review | Verified |

## 5. Master-prompt acceptance requirements

| # | Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- | --- |
| 5.1 | `docs/requirements-traceability.md` | This file | Document review | Verified |
| 5.2 | Disable Swagger/ReDoc/OpenAPI to expose exactly two routes | `app/main.py` | Route test; live 404s | Verified |
| 5.3 | Exact PII placeholders | `app/core/pii.py` | Exact-redaction tests | Verified |
| 5.4 | Exact thresholds 40/80 and inclusive comparisons | `app/core/config.py`, `app/core/policy.py` | Boundary tests at 39/40/41/79/80/81 | Verified |
| 5.5 | Avoid duplicate scoring of same finding | `app/core/scoring.py` deduplicates prompt rules and RAG (rule, doc) | `test_duplicate_prompt_rule_is_not_double_scored` | Verified |
| 5.6 | Multiple detector triggers deterministic | Fixed rule order, fixed tag order, stable reasons | Determinism test; multiple-findings test | Verified |
| 5.7 | CLI must not import detector functions | `cli.py` imports only argparse/json/os/sys/requests | CLI tests; import review | Verified |
| 5.8 | UI must use API, not reimplement logic | `ui/streamlit_app.py` uses `requests` only | AppTest against live API | Verified |
| 5.9 | Separate API and UI services; UI uses Docker service name | `docker-compose.yml`, `Dockerfile.api`, `Dockerfile.ui` | Docker connectivity check | Verified |
| 5.10 | `.dockerignore` and `.gitignore` | Repository root | File review | Verified |
| 5.11 | README covers all required sections | `README.md` | Section review | Verified |
| 5.12 | `docs/design-notes.md` covers architecture, detectors, scoring, policy, sanitization, FP/FN, security, limitations, future | `docs/design-notes.md` | Section review | Verified |
| 5.13 | Realistic `sample_request.json` | Repository root | Live request/response | Verified |
| 5.14 | No authentication, database, queue, accounts, LLM integration | Codebase | Dependency/module review | Verified |
| 5.15 | Do not claim production-grade protection | README and design notes state rule-based prototype limitations | Document review | Verified |
| 5.16 | Final acceptance gate: tests, route count, normal request, injection, PII, RAG, all decisions, CLI, Docker, UI connectivity, docs audit | See README and final report | Local and Docker checks verified | Verified |

## 6. Verification commands used

```bash
# Local tests
.venv/bin/python -m pytest -q

# Live API
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/policy
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" --data @sample_request.json

# CLI
.venv/bin/python cli.py analyze --input sample_request.json --output out.json

# Streamlit (local)
API_BASE_URL=http://127.0.0.1:8000 .venv/bin/python -m streamlit run ui/streamlit_app.py \
  --server.port 8501 --server.address 127.0.0.1 --server.headless true

# Docker
docker compose up --build
docker compose run --rm api pytest -q
```

## 7. Outstanding manual items

- Configure a remote or create a zip if the course portal requires a link/upload;
  the local repository is already initialized and committed.
- Record the 2–3 minute demo if hosting is not provided.

## 8. Docker verification results

The following checks were run in the development environment after the final
image rebuild:

| Check | Command / method | Result |
| --- | --- | --- |
| Compose build and startup | `docker compose up --build` (and a rebuild with `docker compose up --build -d`) | Both images built; API and UI containers started |
| Service status | `docker compose ps` | API `Up ... (healthy)`; UI `Up`; ports `8000` and `8501` published |
| Containerized tests | `docker compose run --rm api pytest -q` | `76 passed, 1 warning` |
| API from host | `curl http://localhost:8000/policy` | HTTP 200 with exact policy JSON |
| UI from host | `curl http://localhost:8501/` and `/_stcore/health` | HTTP 200 |
| UI -> API over Compose network | `docker compose exec -T ui python -c "import requests; ... http://api:8000/policy"` | HTTP 200, policy version `1` |
| UI end-to-end | Streamlit `AppTest` inside the UI container | `block` decision, score 80, `prompt_injection` tag, sanitized prompt returned |
| Container user | `docker compose exec -T api id` / `ui id` | `uid=1000(appuser)` in both containers |
| Route table | Import `app.main` inside the API container | Exactly `POST /analyze` and `GET /policy` |
| CLI against Docker API | `python cli.py analyze --input sample_request.json --output out.json` | Exit 0; valid JSON written |
| Disabled routes | `curl` `/docs`, `/redoc`, `/openapi.json`, `/health` | All HTTP 404 |
| Decision examples | Host `POST /analyze` calls | `allow` (0), `transform` (PII 50 / medium injection 40), `block` (100) all observed |

The Compose stack was stopped after verification with `docker compose down` to
leave the workspace clean. The exact startup command remains
`docker compose up --build`.

