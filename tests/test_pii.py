from __future__ import annotations

from app.core.pii import detect_pii, find_pii, redact_pii


def test_email_detection() -> None:
    matches = find_pii("Contact alice@example.com for details.")
    assert [match.kind for match in matches] == ["email"]


def test_email_redaction_uses_exact_placeholder() -> None:
    assert (
        redact_pii("Email alice@example.com now.")
        == "Email [REDACTED_EMAIL] now."
    )


def test_multiple_emails_are_redacted() -> None:
    text = "Email a@example.com and b@example.org now."
    redacted = redact_pii(text)
    assert redacted.count("[REDACTED_EMAIL]") == 2
    assert "a@example.com" not in redacted
    assert "b@example.org" not in redacted


def test_phone_detection_us_formatted() -> None:
    matches = find_pii("Call (555) 123-4567.")
    assert any(match.kind == "phone" for match in matches)


def test_phone_detection_international() -> None:
    matches = find_pii("Reach me at +44 20 7946 0958.")
    assert any(match.kind == "phone" for match in matches)


def test_phone_redaction_uses_exact_placeholder() -> None:
    assert (
        redact_pii("Call +1 (555) 123-4567.")
        == "Call [REDACTED_PHONE]."
    )


def test_multiple_phone_formats_are_redacted() -> None:
    text = "US 555-123-4567, UK 020 7946 0958, DE +49 30 123456"
    redacted = redact_pii(text)
    assert redacted.count("[REDACTED_PHONE]") == 3


def test_phone_with_country_code_and_compact_number_is_fully_redacted() -> None:
    assert redact_pii("Call +1 5551234567.") == "Call [REDACTED_PHONE]."
    assert redact_pii("Call +44 2079460958.") == "Call [REDACTED_PHONE]."


def test_dates_ids_versions_and_ips_are_not_redacted() -> None:
    text = (
        "Date 2024-01-15, spaced date 2024 01 15 10 30, order 1234567890, "
        "version 1.2.3, IP 192.168.100.1, SSN 123-45-6789"
    )
    assert redact_pii(text) == text


def test_compact_phone_requires_phone_context() -> None:
    assert any(match.kind == "phone" for match in find_pii("Call me at 5551234567."))
    assert find_pii("Order ID 1234567890.") == []


def test_short_local_phone_requires_phone_context() -> None:
    assert any(match.kind == "phone" for match in find_pii("Call me at 555-1234."))
    assert find_pii("Reference 555-1234.") == []


def test_email_requires_a_valid_domain() -> None:
    assert find_pii("user@localhost and @example.com") == []


def test_pii_findings_do_not_expose_values() -> None:
    findings = detect_pii(
        "alice@example.com or +1 (555) 123-4567",
        "prompt",
    )
    assert findings
    for finding in findings:
        assert "alice@example.com" not in finding.evidence
        assert "555" not in finding.evidence
