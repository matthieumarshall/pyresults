---
description: "Use when writing, reviewing, or refactoring Python files. Covers architecture layers, type hints, code style, testing conventions, and security practices for this project."
applyTo: "**/*.py"
---

# Python Coding Standards

## Style & Formatting

- **Formatter / linter**: `ruff` — enforced by pre-commit. Never disable a rule without a comment explaining why.
- All functions and methods must have **type hints** on every parameter and the return type.
- Use `snake_case` for functions and variables, `PascalCase` for classes.
- Maximum line length: 100 characters.
- Prefer explicit `return` types over implicit `None`.

## Module Responsibilities (SOLID)

| Layer | Module | Owns |
|-------|--------|------|
| **Config** | `config/category_config.py` | Category definitions and rules |
| **Config** | `config/competition_config.py` | Competition-wide settings |
| **Domain** | `domain/*.py` | Pure data models and entities — no I/O, no pandas |
| **Repositories** | `repositories/interfaces.py` | Abstract base classes (`IRaceResultRepository`, `IScoreRepository`) |
| **Repositories** | `repositories/csv_*.py` | CSV file reading and writing — one file per entity |
| **Services** | `services/*.py` | Business logic — orchestrates domain objects, depends on repository interfaces |
| **Output** | `output/interfaces.py` | `IOutputGenerator` ABC |
| **Output** | `output/score_data_provider.py` | Loads and formats score data for display |
| **Output** | `output/excel_output_generator.py` / `pdf_output_generator.py` | Format-specific rendering |
| **Orchestrator** | `results_processor.py` | Wires layers together — no business logic |

Never put business logic in `results_processor.py` or output generators. Never put I/O in domain models.

## Domain Models

- Domain entities (`athlete.py`, `category.py`, `race_result.py`, `round.py`, `score.py`, `team.py`) must be pure Python dataclasses or classes — no pandas, no file I/O.
- Use `@dataclass(frozen=True)` for value objects that should not be mutated after creation.
- Enums (e.g. `CategoryType`) live in the domain layer.

## Repository Pattern

- Repositories depend on abstract interfaces (`IRaceResultRepository`, `IScoreRepository`) — never on concrete implementations.
- Each repository reads/writes one kind of entity. Keep the interface minimal.
- Never put pandas logic in service or orchestrator layers — encapsulate it inside the repository.

```python
# Good — service depends on interface
class IndividualScoreService:
    def __init__(self, repo: IScoreRepository) -> None:
        self._repo = repo
```

## Services

- Services receive their dependencies (repositories, config) via constructor injection — no globals.
- One responsibility per service:
  - `RaceProcessorService` — normalise raw race CSV data
  - `IndividualScoreService` — aggregate individual scores across rounds
  - `TeamScoringService` — calculate team results from race results
  - `TeamScoreService` — aggregate team scores across rounds
- Services must not read/write files directly; delegate to repositories.

## Testing

- Tests live in `tests/`; use `pytest`.
- Use `pyfakefs` for filesystem-dependent tests — never read from or write to `input_data/` or `data/` in tests.
- Aim for one test file per source module (e.g. `test_individual_scores.py` covers `IndividualScoreService`).
- Inject fake/stub repositories into services rather than touching real CSV files.
- Run all tests: `uv run pytest tests/`
- Run with coverage: `uv run pytest tests/ --cov=pyresults`

## Security

| Concern | Rule |
|---------|------|
| **SAST** | All Python code must pass `bandit -r pyresults/ -ll`. Add `# nosec B<code>` with an explanation only when a finding is a confirmed false positive. |
| **Dependencies** | Run `uv run pip-audit` before releases to catch known CVEs. Run `uv run pip-licenses` to verify license compliance. |
| **File paths** | Never construct file paths by concatenating user-supplied input. Use `pathlib.Path` and validate paths are within expected directories. |
| **No hardcoded secrets** | Never hardcode credentials, keys, or tokens in source code. |

## Build & Dev Commands

```bash
# Run all quality checks (pre-commit hooks)
uv run pre-commit run --all-files

# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=pyresults

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check

# Security scan
uv run bandit -r pyresults/ -ll --skip B101

# Dependency vulnerability check
uv run pip-audit
```
