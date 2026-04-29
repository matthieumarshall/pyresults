# Keep command behavior consistent on Windows.
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# Sync Python dependencies used by this project.
sync:
    uv sync --all-extras
    uv run python -m pre_commit install

# Run pre-commit hooks on all files.
lint:
    uv run python -m pre_commit run --all-files

# Run the test suite.
test:
    uv run python -m pytest tests/

# Run tests with coverage report.
test-cov:
    uv run python -m pytest tests/ --cov=. --cov-report=xml --junitxml=./test_results.xml

# Build the wheel distribution.
build:
    uv build --wheel

# Tag the current commit with a version and push the tag.
tag version:
    git tag -a "v{{version}}" -m "Release v{{version}}"
    git push origin "v{{version}}"
