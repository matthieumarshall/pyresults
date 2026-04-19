---
name: run-playwright-tests
description: 'Run and debug Playwright UI tests for the login-page project. Use when: executing the test suite, verifying frontend functionality, debugging test failures, checking test coverage.'
argument-hint: 'Optional: specific test file or test name to run'
---

# Running Playwright Tests

This skill provides a workflow for executing, debugging, and fixing Playwright UI tests in the login-page project.

## When to Use

- Running the full UI test suite or specific tests
- Debugging test failures (console errors, network issues, element visibility)
- Verifying CSS or JavaScript changes don't break existing behaviour
- Adding new UI tests for features or components
- Checking that authentication, HTMX swaps, and modal interactions work end-to-end

## Prerequisites

- Ensure all dependencies are installed: `uv sync`
- Backend application must be running on `http://localhost:8000` (tests start the server automatically)
- No conflicting processes on port 8000

## Test Organization

Tests are located in `tests/ui/`:
- `test_login_flow.py` — Login and authentication flow
- `test_rules_editor.py` — Quill editor integration
- `test_sidebar_navigation.py` — Navigation menu and routing
- `test_fixture_images.py` — Course map image gallery and modal (fixture-images.js)
- `conftest.py` — Shared fixtures: `browser`, `admin_browser`, `server_process`, `admin_auth_state`

## Quick Start: Run All Tests

```bash
uv run pytest tests/ui/ -v
```

Output shows pass/fail for each test and timing. A test session fixture starts the FastAPI server once per session.

## Run Specific Tests

By file:
```bash
uv run pytest tests/ui/test_fixture_images.py -v
```

By test name (includes substring):
```bash
uv run pytest tests/ui/ -k "modal" -v
```

By class:
```bash
uv run pytest tests/ui/test_fixture_images.py::TestFixtureImageModal -v
```

## Debugging Failures

### 1. Check Server Startup

If tests hang on `server_process`, the server may have failed to start:

```bash
# Run server manually to see startup errors
uv run uvicorn website.main:app --reload
```

Fix issues in `.github/copilot-instructions.md` or `pyproject.toml`, then retry.

### 2. Inspect Test Logs

Playwright captures console errors and page errors in the fixture:

```python
page_errors: list[str] = []
admin_browser.on("pageerror", lambda e: page_errors.append(str(e)))
admin_browser.goto(url)
assert not page_errors, f"Uncaught JS errors: {page_errors}"
```

Look for missing routes, failed asset loads, or script errors.

### 3. Debug Network Requests

```python
failed_requests: list[str] = []
admin_browser.on(
    "response",
    lambda r: failed_requests.append(f"{r.url} -> {r.status}")
    if r.status >= 400
    else None,
)
```

Check that XHR/fetch requests return 2xx, CSRF token validation passes, and HTMX routes return the correct HTML fragments.

### 4. Run with Screenshots
