# SentraGuard Lite — Design Notes

## 1. Architectural decisions

### Pure core, thin boundaries

The security logic is split into small pure functions:

- `detect_prompt_injection(text) -> list[Finding]`
- `detect_pii(text, location) -> list[Finding]`
- `detect_rag_injection(text, doc_id) -> list[Finding]`
- `score_findings(findings) -> int`
- `decide(score) -> "allow" | "transform" | "block"`
- `sanitize_prompt(text)` / `sanitize_context_doc(text, doc_id)`

FastAPI only validates the request, calls the analyzer, logs non-sensitive
metadata, and returns the Pydantic response. The CLI and UI call the API rather
than importing detector code. This keeps the security logic independently
testable and prevents the interfaces from drifting from the API contract.

### Exactly two routes

The app is created with `docs_url=None`, `redoc_url=None`, and
`openapi_url=None`. The only `APIRoute` objects are `POST /analyze` and
`GET /policy`. There is no custom health endpoint; the Compose health check uses
`GET /policy`.

### Central configuration

Policy version, detector names, thresholds, and detector weights live in
`app/core/config.py`. The API's `GET /policy` and the scoring engine read the
same constants, so the published policy and the enforced policy cannot diverge.

### No persistence, no external calls

The gateway is stateless. It does not store prompts, documents, findings, or
responses. It makes no outbound network calls. This keeps the demo reproducible
and reduces the privacy surface. The tradeoff is that there is no audit trail;
production would add a privacy-preserving audit log.

## 2. Detectors

### 2.1 Prompt injection / jailbreak

Text is normalized before matching:

- Unicode NFKC;
- zero-width and bidirectional control characters removed;
- curly quotes normalized;
- lowercasing;
- whitespace collapsed.

Rules are defined in `app/core/patterns.py` and grouped by severity. The rule
families cover:

- ignoring/forgetting/disregarding previous instructions;
- overriding system, developer, safety, or policy instructions;
- revealing system/developer/hidden prompts;
- DAN / "do anything now" / jailbreak or developer mode;
- bypassing or disabling safety filters;
- replacing the model with an unrestricted persona;
- fake new-instruction headers;
- refusing to follow guidelines;
- leaking text that appeared before the user turn;
- instruction-hierarchy manipulation;
- asking for the system prompt;
- demanding personal obedience.

Each rule has a stable id, a weight, and a short description. The detector
reports at most one finding per rule per text, so repeating the same phrase does
not inflate the score.

#### Meta-discussion suppression

A sentence that contains discussion markers such as "prompt injection",
"jailbreak", "for example", "such as", "example:", "test case", "detect",
"mitigate", "defend", "is when", "refers to", or "definition" is treated as
discussion rather than an attempt. URLs and email addresses are stripped before
this check so a domain such as `evil.example` does not accidentally look like
the word "example". Matches inside double quotes or backticks are also
suppressed. This prevents ordinary training material such as:

> Prompt injection is an attack where a user tries to make a model ignore
> previous instructions. We detect this with rules.

from being blocked. It is a heuristic with a deliberate tradeoff: an attacker can
frame an attack as an example and evade detection. A production system should
combine this with model-based classification, provenance, and multi-turn
analysis.

### 2.2 PII detection and redaction

#### Email

The email pattern requires:

- a local part of 1–64 characters that starts and ends with an alphanumeric;
- an `@`;
- one or more domain labels that do not start or end with a hyphen;
- a 2–24 letter TLD;
- lookarounds that prevent matches inside words, malformed addresses, and longer
  dotted tokens.

This avoids matching `user@localhost`, `@example.com`, `user@example.c`, and
`user@example.com.evil`.

#### Phone

Formatted candidates must contain at least one separator. The detector accepts
common forms such as:

- `+1 (555) 123-4567`
- `+1-555-123-4567`
- `(555) 123-4567`
- `555-123-4567`
- `555.123.4567`
- `+44 20 7946 0958`
- `020 7946 0958`
- `+49 30 123456`

Validation rejects:

- dates such as `2024-01-15`;
- IPv4 addresses such as `192.168.100.1`;
- SSN-shaped values such as `123-45-6789`;
- 7–9 digit numbers with separators unless nearby telephony context exists;
- dotted numeric sequences that look like versions or IPs;
- slices of longer dotted/hyphenated numeric sequences;
- formatted numbers near labels such as "version", "order", "invoice",
  "account", "reference", "id", "isbn", "date", "tracking", or "serial" unless
  nearby telephony context overrides the label.

Unformatted 10–15 digit strings are ambiguous, so they are only accepted when
nearby text contains a telephony word such as "phone", "call", "mobile", "text",
"contact", or "fax" (or when the value starts with `+`). This intentionally
misses some unformatted phone numbers in exchange for not redacting order IDs and
account numbers. That tradeoff is documented in the README.

#### Redaction

Detected spans are replaced with the exact placeholders:

- `[REDACTED_EMAIL]`
- `[REDACTED_PHONE]`

Email spans are collected first, and phone spans that overlap an email span are
skipped. The raw values are not retained in `PIIMatch` and are never included in
`reasons` or logs.

### 2.3 RAG injection

Each context document is analyzed independently. The detector combines the
prompt-injection rule set with RAG-specific rules for:

- revealing secrets, passwords, API keys, tokens, or credentials;
- sending/uploading data to an external URL or email address;
- asserting that the model must comply;
- claiming system/developer authorization.

It also checks header-like lines such as:

- `SYSTEM: ...`
- `DEVELOPER: ...`
- `<system>`
- `### SYSTEM`

A header is treated as malicious when it is followed by directive language
(`ignore`, `you are`, `override`, `reveal`, `password`, `token`, etc.), or when
it is a bracketed/markdown header with little or no trailing text. A benign line
such as `System: Ubuntu 22.04` is not treated as an injection header because it
has no directive language. A bare uppercase `SYSTEM:` is treated as suspicious.

The document id is included in the evidence, and document order is preserved in
the response. A benign user prompt with a malicious retrieved document still
triggers `rag_injection`.

## 3. Risk scoring

### 3.1 Formula

For a set of findings:

```text
prompt_score = min(100, sum of distinct prompt rule weights)
rag_score    = min(100, sum of distinct (rule, document) weights)
pii_score    = 0 if no PII
               else min(60, 40 + 10 * (pii_occurrences - 1))
risk_score   = min(100, prompt_score + rag_score + pii_score)
```

The caps prevent repeated matches from producing unbounded scores. The
per-rule deduplication prevents the same finding from being counted twice within
one text. The same RAG rule in two different documents is counted separately
because each document is an independent retrieved source.

### 3.2 Weights and rationale

| Category | Severity | Weight |
| --- | --- | --- |
| Prompt injection | Critical | 80 |
| Prompt injection | High | 55 |
| Prompt injection | Medium | 40 |
| RAG injection | Critical | 80 |
| RAG injection | High | 55 |
| RAG injection | Fake system header | 55 |
| PII | First occurrence | 40 |
| PII | Each additional occurrence | +10, cap 60 |

Rationale:

- A single critical injection (for example, "ignore previous instructions")
  should block, not merely transform. 80 reaches the block threshold.
- High and medium findings transform on their own, but two high findings or a
  high plus PII can reach 80 and block.
- PII is sensitive but usually should be redacted, not blocked. The first
  occurrence reaches the transform threshold; additional occurrences increase
  the score, but the 60 cap means PII alone can never block.
- The total is capped at 100, so combinations cannot exceed the contract.

### 3.3 Threshold behavior

The comparison is inclusive:

| Score | Decision |
| --- | --- |
| 0–39 | `allow` |
| 40–79 | `transform` |
| 80–100 | `block` |

Tests cover 39, 40, 41, 79, 80, and 81 explicitly.

## 4. Policy decisions

### Allow

Return the original prompt and documents unchanged. Harmless text is not
rewritten. With the current weights, `allow` implies no findings, so there is
nothing to redact.

### Transform

Return sanitized content. PII is replaced with the mandated placeholders.
Detected injection sentences are replaced with:

- `[REDACTED_PROMPT_INJECTION]` for the prompt;
- `[REDACTED_RAG_INJECTION]` for a context document.

Document ids and order are preserved. Reasons explain which rule fired.

### Block

Mark the request as blocked. The response still contains sanitized content; it
does not expose raw PII or carry the detected injection sentence forward. A
caller should not use a blocked request's content as a model input. The response
is not represented as allowed.

## 5. Sanitization behavior

Sanitization is applied to the prompt and every context document before the
response is built, including for blocked requests. The sanitizer splits text
into sentence/line units while preserving separators. A unit that independently
triggers the relevant detector is replaced with the placeholder. If the full
text triggers but no individual unit does (for example, a rule split across
sentences), the whole text is replaced. This is conservative for content that
has already been classified as risky.

PII redaction is applied after injection neutralization. If a malicious sentence
contains PII, the whole sentence is replaced, so the PII is removed along with
it. PII findings are still counted in the risk score because detection is
performed on the original text.

Limitations:

- The sanitizer does not semantically rewrite text; it removes the offending
  sentence/line.
- It may remove harmless text that shares a sentence with an attack.
- It does not attempt to neutralize obfuscated attacks that the detector missed.

## 6. False positives and false negatives

### Likely false positives

- A benign sentence that says "ignore previous instructions" in a context that
  does not contain a meta-discussion marker.
- A technical document with a header such as `SYSTEM:` followed by directive-like
  words.
- A version or numeric identifier that looks like a formatted phone number and is
  not near a non-phone label.
- A legitimate email address in a context where redaction is not desired; the
  gateway always redacts detected email addresses.

### Likely false negatives

- Paraphrased injection that does not use the rule vocabulary.
- Attacks encoded in base64, leetspeak, homoglyphs, or another language.
- Attacks split across multiple turns or multiple documents.
- An attack deliberately framed as an example or quotation.
- Unformatted phone numbers without nearby telephony context.
- PII types outside email and phone (names, addresses, government ids).

The design intentionally favors explainability and deterministic behavior over
recall. It is not a replacement for a production guardrail platform.

## 7. Security assumptions

- The API is an internal service. There is no authentication, authorization,
  rate limiting, or TLS in this MVP.
- Clients are trusted to send well-formed JSON; Pydantic enforces the schema at
  the boundary.
- The gateway does not execute retrieved content, call tools, or forward content
  to an LLM.
- Logs are non-sensitive by design: request id (sanitized/truncated), decision,
  score, and tags. Raw prompts and documents are not logged.
- No secrets are stored in the repository or images.
- The Docker images run as a non-root user.
- The service is stateless; there is no database or filesystem persistence of
  user content.

## 8. Known limitations

- Rule-based detection is not comprehensive.
- The meta-discussion heuristic is evadable.
- PII regexes cover common formats, not every legal/format variation.
- The phone heuristic intentionally misses some compact numbers.
- Sanitization is sentence/line based and may remove adjacent harmless text.
- No authentication, rate limiting, request-size limits, audit log, or metrics.
- No multilingual support or model-based classification.
- No output-side guardrails; only input and retrieved-context analysis.
- No protection against prompt injection that arrives through metadata fields;
  metadata is treated as identifiers, not content.

## 9. Future improvements / production hardening

1. **Authentication and authorization** for callers, with per-tenant policy.
2. **Rate limiting and request-size limits** at the API gateway and application.
3. **Structured audit logging** with hashed request ids, timestamps, decisions,
   and rule ids — never raw content.
4. **Policy configuration** loaded from a signed config file or database, with
   versioning and rollback.
5. **Model-based classifiers** combined with rules for paraphrase and multilingual
   detection.
6. **Provenance and trust scoring** for retrieved documents, including source
   allowlists and signed retrieval metadata.
7. **Canary tokens and output filtering** to detect system-prompt leakage.
8. **Red-team corpus and regression tests** for evasion techniques, including
   encoding and homoglyph attacks.
9. **Metrics and alerting** on block rates, detector hit rates, and false-positive
   reports.
10. **Container hardening**: read-only root filesystem, dropped capabilities,
    network policies, SBOM generation, and dependency/image scanning.
11. **TLS termination** and a reverse proxy in front of the API.
12. **Human review workflow** for blocked requests in high-risk applications.
