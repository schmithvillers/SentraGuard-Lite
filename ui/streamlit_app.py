"""Streamlit UI for SentraGuard Lite.

The UI is intentionally thin: it collects a request, calls the FastAPI service,
and renders the response.  All security logic remains in the API.
"""

from __future__ import annotations

import os
import uuid

import requests
import streamlit as st
import os
import streamlit as st

def get_api_base_url():
    # First, read Streamlit Cloud Secrets
    try:
        url = st.secrets.get("API_BASE_URL")
    except Exception:
        url = None

    # Fall back to environment variable
    if not url:
        url = os.getenv("API_BASE_URL")

    # Local Docker fallback
    if not url:
        url = "http://api:8000"

    return url.rstrip("/")


API_BASE_URL = get_api_base_url()
REQUEST_TIMEOUT_SECONDS = 20
POLICY_TIMEOUT_SECONDS = 3

st.set_page_config(
    page_title="SentraGuard Lite",
    page_icon="🛡️",
    layout="wide",
)


def fetch_policy() -> dict | None:
    try:
        response = requests.get(
            f"{API_BASE_URL}/policy", timeout=POLICY_TIMEOUT_SECONDS
        )
    except requests.exceptions.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def validation_messages(body: object) -> list[str]:
    """Extract readable validation messages without echoing raw input."""

    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, list):
        messages: list[str] = []
        for item in detail:
            if not isinstance(item, dict):
                continue
            location = ".".join(str(part) for part in item.get("loc", []))
            message = item.get("msg", "invalid value")
            messages.append(f"{location}: {message}" if location else message)
        return messages
    if isinstance(detail, str):
        return [detail]
    return []


if "request_id_input" not in st.session_state:
    st.session_state.request_id_input = f"req-{uuid.uuid4().hex[:8]}"
if "policy" not in st.session_state:
    st.session_state.policy = fetch_policy()
if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.header("🛡️ SentraGuard Lite")
    st.caption("Deterministic, offline guardrails gateway")
    st.divider()
    st.subheader("API")
    st.code(API_BASE_URL, language=None)
    if st.button("Refresh policy", use_container_width=True):
        st.session_state.policy = fetch_policy()

    policy = st.session_state.get("policy")
    if isinstance(policy, dict):
        st.caption(f"Policy version: {policy.get('version', '?')}")
        detectors = policy.get("detectors", [])
        st.write("Detectors: " + ", ".join(str(item) for item in detectors))
        thresholds = policy.get("thresholds", {})
        if isinstance(thresholds, dict):
            st.write(f"Transform ≥ {thresholds.get('transform_score', '?')}")
            st.write(f"Block ≥ {thresholds.get('block_score', '?')}")
    else:
        st.caption("Policy not loaded. Is the API running?")

    st.divider()
    st.caption(
        "Set API_BASE_URL to point the UI at another API. "
        "Under Docker Compose it is http://api:8000."
    )

st.title("SentraGuard Lite")
st.caption(
    "Analyze a prompt and up to three retrieved context documents for prompt "
    "injection, PII, and RAG injection."
)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Request")
    prompt = st.text_area(
        "Prompt",
        height=180,
        placeholder="Enter the user prompt to analyze...",
    )

    st.markdown("**Metadata**")
    meta_left, meta_mid, meta_right = st.columns(3)
    app_id = meta_left.text_input("app_id", value="sentraguard-demo", key="app_id")
    user_id = meta_mid.text_input("user_id", value="demo-user", key="user_id")
    request_id = meta_right.text_input("request_id", key="request_id_input")

    num_docs = st.number_input(
        "Context documents (0–3)",
        min_value=0,
        max_value=3,
        value=0,
        step=1,
    )

    context_docs: list[dict[str, str]] = []
    for index in range(int(num_docs)):
        with st.expander(f"Context document {index + 1}", expanded=True):
            doc_id = st.text_input(
                "Document ID",
                value=f"doc-{index + 1}",
                key=f"doc_id_{index}",
            )
            doc_text = st.text_area(
                "Document text",
                height=100,
                key=f"doc_text_{index}",
            )
        context_docs.append({"id": doc_id, "text": doc_text})

    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

    if analyze_clicked:
        if not prompt.strip():
            st.error("Prompt must not be empty.")
        else:
            payload = {
                "prompt": prompt,
                "context_docs": context_docs,
                "metadata": {
                    "app_id": app_id,
                    "user_id": user_id,
                    "request_id": request_id,
                },
            }
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze",
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    f"Could not connect to the API at {API_BASE_URL}. "
                    "Is the API running?"
                )
            except requests.exceptions.Timeout:
                st.error(
                    "The API request timed out after "
                    f"{REQUEST_TIMEOUT_SECONDS} seconds."
                )
            except requests.exceptions.RequestException as exc:
                st.error(f"API request failed: {exc}")
            else:
                if response.status_code == 200:
                    try:
                        body = response.json()
                    except ValueError:
                        st.error("The API returned invalid JSON.")
                    else:
                        if isinstance(body, dict):
                            st.session_state.result = body
                        else:
                            st.error("The API response was not a JSON object.")
                elif response.status_code == 422:
                    st.error(
                        "The API rejected the request (HTTP 422). "
                        "Check required fields and types."
                    )
                    try:
                        messages = validation_messages(response.json())
                    except ValueError:
                        messages = []
                    if messages:
                        with st.expander("Validation details"):
                            for message in messages:
                                st.write(f"- {message}")
                else:
                    st.error(f"The API returned HTTP {response.status_code}.")

with right:
    st.subheader("Result")
    result = st.session_state.get("result")

    if not isinstance(result, dict):
        st.info("Submit a request to see the policy decision and sanitized output.")
    else:
        decision = result.get("decision", "unknown")
        risk_score = result.get("risk_score", 0)
        risk_tags = result.get("risk_tags", [])
        reasons = result.get("reasons", [])
        sanitized_prompt = result.get("sanitized_prompt", "")
        sanitized_docs = result.get("sanitized_context_docs", [])

        if decision == "allow":
            st.success("ALLOW — no policy action required")
        elif decision == "transform":
            st.warning("TRANSFORM — content was sanitized before use")
        elif decision == "block":
            st.error("BLOCK — request rejected by policy")
        else:
            st.info(f"Decision: {decision}")

        metric_left, metric_mid, metric_right = st.columns(3)
        metric_left.metric("Decision", str(decision).upper())
        metric_mid.metric("Risk score", f"{risk_score}/100")
        metric_right.metric("Risk tags", len(risk_tags) if isinstance(risk_tags, list) else 0)

        if isinstance(risk_tags, list) and risk_tags:
            st.markdown(
                "**Risk tags:** " + ", ".join(f"`{tag}`" for tag in risk_tags)
            )
        else:
            st.markdown("**Risk tags:** none")

        st.markdown("**Reasons**")
        if isinstance(reasons, list) and reasons:
            st.dataframe(reasons, use_container_width=True, hide_index=True)
        else:
            st.caption("No detector findings.")

        st.markdown("**Sanitized prompt**")
        st.code(
            str(sanitized_prompt) or "(empty)",
            language=None,
            wrap_lines=True,
        )

        st.markdown("**Sanitized context documents**")
        if isinstance(sanitized_docs, list) and sanitized_docs:
            for index, document in enumerate(sanitized_docs):
                if not isinstance(document, dict):
                    continue
                with st.expander(
                    f"{document.get('id', f'doc-{index + 1}')}",
                    expanded=False,
                ):
                    st.code(
                        str(document.get("text", "")) or "(empty)",
                        language=None,
                        wrap_lines=True,
                    )
        else:
            st.caption("No context documents were supplied.")

        with st.expander("Raw JSON response"):
            st.json(result)
