# SentraGuard Lite --- Submission Evidence Checklist

Use this document as the evidence register for the final assignment
submission.

For every checklist item: - Mark the checkbox only after you have
verified the requirement. - Add proof in the **Evidence** field:
screenshot path, repository file path, command output, test result, or
hosted URL. - Store screenshots in the repository's `screenshots/`
folder. - Use repository-relative paths so the evidence remains valid
when the project is shared. - Do not mark an item complete merely
because the code exists. Run or inspect it and capture evidence.

Suggested evidence folder structure:

``` text
screenshots/
├── dashboard/
├── api/
├── cli/
├── docker/
├── tests/
└── security/
```

You can use different filenames, but keep them descriptive and update
the paths below to match the actual files.

------------------------------------------------------------------------

## 1. Deliverables

### 1.1 Git repository link or ZIP shared

-   [ ] A Git repository link or submission ZIP has been prepared and
    shared.

**Evidence to add:** - Repository URL: `[PASTE REPOSITORY URL HERE]` -
OR ZIP file path/name: `[PASTE ZIP PATH OR FILE NAME HERE]` - Optional
screenshot: `screenshots/[ADD REPOSITORY OR ZIP SCREENSHOT HERE]`

**Verification notes:** Confirm the shared repository/ZIP contains the
application source, tests, Docker files, README, design notes, sample
request, and required evidence. Exclude virtual environments, caches,
secrets, and unrelated files.

### 1.2 Working FastAPI service with exactly two specified endpoints

-   [ ] FastAPI service starts successfully.
-   [ ] `POST /analyze` works.
-   [ ] `GET /policy` works.
-   [ ] No additional application endpoints are exposed.

**Evidence to add:** - Route implementation: `app/main.py` (confirm
actual path) - API test files: `tests/[ADD RELEVANT TEST FILES HERE]` -
Route-list verification output:
`[ADD TERMINAL OUTPUT FILE OR SCREENSHOT PATH]` - `GET /policy` proof:
`screenshots/api/[ADD POLICY RESPONSE SCREENSHOT]` - `POST /analyze`
proof: `screenshots/api/[ADD ANALYZE RESPONSE SCREENSHOT]`

**Verification command:**

``` bash
curl -i http://localhost:8000/policy
```

For the route-count proof, add the exact command or test used to inspect
the FastAPI application's registered routes:

`[ADD ROUTE VERIFICATION COMMAND OR TEST NAME HERE]`

### 1.3 Working Streamlit UI

-   [ ] Streamlit UI opens successfully.
-   [ ] UI can submit a prompt to the API.
-   [ ] UI supports zero to three context documents.
-   [ ] UI displays the decision, risk score, tags, reasons, and
    sanitized output.
-   [ ] UI handles API errors clearly.

**Evidence to add:** - UI implementation: `ui/streamlit_app.py` (confirm
actual path) - Main dashboard screenshot:
`screenshots/dashboard/[ADD DASHBOARD SCREENSHOT]` - Successful analysis
screenshot:
`screenshots/dashboard/[ADD SUCCESSFUL ANALYSIS SCREENSHOT]` -
Context-document test screenshot:
`screenshots/dashboard/[ADD CONTEXT DOCUMENT SCREENSHOT]` -
Error-handling screenshot, if captured:
`screenshots/dashboard/[ADD ERROR SCREENSHOT]`

### 1.4 Working CLI command

-   [ ] The required CLI command works against the running API.
-   [ ] CLI reads the input JSON file.
-   [ ] CLI writes the API response to the requested output file.
-   [ ] CLI reports failures clearly.

**Required command:**

``` bash
python cli.py analyze --input sample_request.json --output out.json
```

**Evidence to add:** - CLI implementation: `cli.py` - Input file:
`sample_request.json` - Generated output file: `out.json` (include only
if appropriate for the submission) - Terminal screenshot:
`screenshots/cli/[ADD CLI SUCCESS SCREENSHOT]` - Output inspection
proof: `screenshots/cli/[ADD OUTPUT JSON SCREENSHOT]`

### 1.5 Docker Compose works without manual edits

-   [ ] Docker images build successfully.
-   [ ] Both API and UI services start using the supplied Compose
    configuration.
-   [ ] No manual source/configuration edits are needed after startup.

**Required command:**

``` bash
docker compose up --build
```

**Evidence to add:** - Compose configuration: `docker-compose.yml` or
`compose.yaml` (use the actual filename) - API Dockerfile:
`Dockerfile.api` - UI Dockerfile: `Dockerfile.ui` - Terminal screenshot
showing successful build/start:
`screenshots/docker/[ADD DOCKER BUILD AND STARTUP SCREENSHOT]` -
Optional service status output:
`[ADD docker compose ps OUTPUT OR SCREENSHOT]`

### 1.6 API reachable at localhost:8000

-   [ ] API is reachable at `http://localhost:8000`.
-   [ ] `GET /policy` returns a successful response.

**Evidence to add:** - API response screenshot:
`screenshots/api/[ADD LOCALHOST 8000 SCREENSHOT]` - Command output or
test: `[ADD CURL OUTPUT OR TEST REFERENCE]`

### 1.7 UI reachable at localhost:8501

-   [ ] UI is reachable at `http://localhost:8501`.
-   [ ] UI successfully communicates with the API.

**Evidence to add:** - Browser screenshot:
`screenshots/dashboard/[ADD LOCALHOST 8501 SCREENSHOT]` - End-to-end
analysis screenshot:
`screenshots/dashboard/[ADD UI TO API FLOW SCREENSHOT]`

### 1.8 Hosted demo or screen recording

Complete at least one of the following:

-   [ ] Hosted demo URL(s) provided.
-   [ ] A 2--3 minute screen recording showing the full flow is
    prepared.

**Evidence to add:** - Hosted API URL:
`[PASTE URL OR WRITE NOT APPLICABLE]` - Hosted UI URL:
`[PASTE URL OR WRITE NOT APPLICABLE]` - Recording file path:
`[ADD RECORDING FILE PATH]` - OR recording link:
`[PASTE SHAREABLE RECORDING LINK]`

**Suggested recording contents:** Start the application, show the UI,
submit a benign request, demonstrate PII redaction, demonstrate
prompt-injection detection, demonstrate a malicious retrieved context
document, run the CLI, and show the test result. Keep the recording
within 2--3 minutes.

------------------------------------------------------------------------

## 2. Tests

### 2.1 Ten required pytest tests included

-   [ ] At least ten meaningful pytest tests are included.
-   [ ] Tests cover the required core behavior and assignment scenarios.

**Evidence to add:** - Test directory: `tests/` - Test files:
`[LIST ACTUAL TEST FILES HERE]` - Test count / collection output:
`screenshots/tests/[ADD PYTEST COLLECTION OR SUMMARY SCREENSHOT]`

### 2.2 Tests pass locally or in Docker

Choose the method actually used:

-   [ ] Local test run passes.
-   [ ] Docker test run passes.

**Commands:**

``` bash
pytest -q
```

OR

``` bash
docker compose run --rm api pytest -q
```

**Evidence to add:** - Exact command run: `[PASTE COMMAND]` - Actual
result, including passed/failed/skipped counts:
`[PASTE ACTUAL TEST SUMMARY]` - Terminal screenshot:
`screenshots/tests/[ADD PASSING TEST SUITE SCREENSHOT]`

Do not enter a test count based on an earlier run. Record the result
from the final version being submitted.

------------------------------------------------------------------------

## 3. Documentation

### 3.1 README.md

-   [ ] `README.md` includes a project summary explaining what the
    application does.
-   [ ] README explains how to run the application with Docker.
-   [ ] README explains how to run tests.
-   [ ] README explains how to run the CLI.
-   [ ] README explains how to use the UI.
-   [ ] README includes sample inputs and outputs.

**Evidence to add:** - File: `README.md` - Optional screenshot of
rendered README: `screenshots/[ADD README SCREENSHOT]` - Sample request:
`sample_request.json` - Sample output:
`[ADD ACTUAL SAMPLE OUTPUT FILE PATH, IF INCLUDED]`

### 3.2 Design Notes section

-   [ ] Design Notes describe the assumptions.
-   [ ] Design Notes explain the implementation tradeoffs.
-   [ ] Design Notes document limitations.
-   [ ] Design Notes identify next steps for production.

**Evidence to add:** - File and section: `README.md` → `Design Notes` -
OR separate document: `docs/design-notes.md` - Optional screenshot:
`screenshots/[ADD DESIGN NOTES SCREENSHOT]`

### 3.3 Dashboard test-results report

-   [ ] Dashboard test results are documented.
-   [ ] Screenshots are embedded using relative Markdown paths.
-   [ ] All referenced screenshot files exist in the repository.

**Evidence to add:** - Report: `result.md` - Screenshot directory:
`screenshots/` - Optional rendered report screenshot:
`screenshots/[ADD RESULT REPORT PREVIEW SCREENSHOT]`

------------------------------------------------------------------------

## 4. Security and quality

### 4.1 No secrets committed

-   [ ] No API keys, tokens, passwords, or other secrets are committed.
-   [ ] `.gitignore` excludes local environment files and sensitive
    artifacts where appropriate.
-   [ ] Repository has been reviewed for accidental secrets.

**Evidence to add:** - Ignore rules: `.gitignore` - Secret scan
command/tool and actual result: `[ADD TOOL, COMMAND, AND RESULT]` -
Optional screenshot:
`screenshots/security/[ADD SECRET SCAN RESULT SCREENSHOT]`

Do not paste actual secrets into this checklist. If a secret is
discovered, remove it from the repository and rotate/revoke it as
appropriate; deleting it from the latest file alone may not remove it
from Git history.

### 4.2 No unintended raw PII storage or logging

-   [ ] Raw PII is not unintentionally written to logs or persistent
    storage.
-   [ ] Sanitized response fields use the required redaction behavior.
-   [ ] Blocked responses do not expose sensitive values through fields
    intended to be sanitized.

**Evidence to add:** - Relevant implementation files:
`app/core/[ADD DETECTOR OR REDACTION FILE PATHS]` - Logging
implementation: `[ADD LOGGING FILE PATH OR STATE NONE]` - PII test
references: `tests/[ADD RELEVANT TEST FILES]` - PII dashboard proof:
`screenshots/dashboard/Screenshot 2026-10-30 at 1.31.10 PM.png` -
Combined attack proof:
`screenshots/dashboard/Screenshot 2026-10-30 at 1.33.22 PM.png`

### 4.3 Deterministic behavior and offline/mock operation

-   [ ] Core analysis works without an external LLM API.
-   [ ] Repeated identical inputs produce consistent outputs.
-   [ ] No network connection is required for core analysis after
    dependencies are installed.

**Evidence to add:** - Detector/scoring implementation:
`app/core/[ADD RELEVANT FILE PATHS]` - Determinism test:
`tests/[ADD TEST FILE AND TEST NAME]` - Offline behavior verification:
`[ADD COMMAND, TEST, OR NOTES]`

### 4.4 Clear error messages for invalid inputs

-   [ ] Invalid request bodies produce clear errors.
-   [ ] Invalid CLI input produces a useful error.
-   [ ] API connection failures are handled clearly by the CLI and UI.

**Evidence to add:** - API validation tests: `tests/[ADD TEST FILE]` -
CLI error tests: `tests/[ADD TEST FILE]` - UI error-handling
implementation: `ui/streamlit_app.py` - Optional screenshots:
`screenshots/security/[ADD INVALID INPUT OR ERROR SCREENSHOTS]`

------------------------------------------------------------------------

## 5. Final verification

These are the end-to-end checks listed in the assignment. Record the
actual evidence for each one.

### 5.1 Docker Compose starts successfully

-   [ ] `docker compose up --build` completes successfully.
-   [ ] API and UI services remain available after startup.

**Evidence:** `screenshots/docker/[ADD FINAL DOCKER STARTUP SCREENSHOT]`

### 5.2 UI triggers the core flow end-to-end

-   [ ] A request submitted in the UI reaches the API.
-   [ ] The UI displays the API's analysis response.

**Evidence:** `screenshots/dashboard/[ADD END TO END SCREENSHOT]`

### 5.3 CLI works against the running API

-   [ ] The required CLI command successfully submits a request and
    writes the response.

**Evidence:** `screenshots/cli/[ADD CLI END TO END SCREENSHOT]`

### 5.4 Tests pass and cover core logic

-   [ ] Detector tests pass.
-   [ ] Redaction tests pass.
-   [ ] Risk-scoring and policy tests pass.
-   [ ] API tests pass.
-   [ ] CLI tests pass where included.

**Evidence:** `screenshots/tests/[ADD FINAL TEST SUMMARY SCREENSHOT]`

### 5.5 Code is readable and maintainable

-   [ ] Modules have clear responsibilities.
-   [ ] Names and type hints are understandable.
-   [ ] Unnecessary duplication and dead code have been reviewed.
-   [ ] Dependencies are appropriate and documented.
-   [ ] No debug code or accidental temporary files remain.

**Evidence to add:** - Repository structure:
`[ADD REPOSITORY TREE OR FILE PATH]` - Code review notes:
`[ADD SHORT NOTES OR LINK TO REVIEW]` - Optional screenshot:
`screenshots/[ADD REPOSITORY STRUCTURE SCREENSHOT]`

------------------------------------------------------------------------

## 6. Final submission record

Complete this section immediately before submitting.

  Submission detail            Value
  ---------------------------- -----------------------------------------------
  Project name                 SentraGuard Lite
  Repository URL               `[PASTE URL]`
  Submission ZIP               `[ADD FILE NAME OR NOT APPLICABLE]`
  Hosted demo URL              `[PASTE URL OR NOT APPLICABLE]`
  Screen recording link/path   `[PASTE LINK OR PATH]`
  Final test command           `[PASTE COMMAND]`
  Final test result            `[PASTE ACTUAL PASSED/FAILED/SKIPPED COUNTS]`
  Date of final verification   `[YYYY-MM-DD]`

### Final sign-off

-   [ ] All mandatory checklist items have been verified.
-   [ ] Every completed item has supporting evidence or a clear file
    reference.
-   [ ] All screenshot paths in this document resolve.
-   [ ] All Markdown links and embedded images render.
-   [ ] No placeholders remain in mandatory evidence fields.
-   [ ] The repository or ZIP is ready to share.

**Outstanding items / exceptions:**

`[LIST ANY INCOMPLETE ITEMS, KNOWN LIMITATIONS, OR WRITE "NONE" AFTER VERIFYING]`

------------------------------------------------------------------------

*This checklist is an evidence register for the SentraGuard Lite
assignment. It does not replace the official assignment specification or
submission checklist. The official requirements remain authoritative.*
