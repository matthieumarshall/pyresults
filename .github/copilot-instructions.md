# Copilot Instructions for pyresults

## Project Overview
pyresults is a Python application for processing and generating standings for the Oxfordshire Cross Country League. It processes race results from CSV files, calculates individual and team scores across multiple rounds, and produces Excel and PDF outputs with league standings. The codebase follows SOLID principles with clean architecture layers (domain, repositories, services, output).

## Tech Stack
- **Python**: >=3.10
- **Package Manager**: uv (modern Python package manager)
- **Build System**: hatchling with hatch scripts
- **Key Dependencies**:
  - pandas 2.2.3 - Data processing and CSV handling
  - fpdf 1.7.2 - PDF generation
  - openpyxl 3.1.2 - Excel file creation
  - numpy >=1.26.0,<2.0 - Numerical operations
  - python-dateutil 2.8.2
- **Development Tools**:
  - pytest - Testing framework
  - ruff - Linting and formatting
  - ty - Type checking (Red Knot-based, from Astral)
  - pre-commit - Git hooks

## Pre-commit Hooks
The project enforces quality via pre-commit hooks (`.pre-commit-config.yaml`):

1. **pre-commit-hooks** — general file hygiene (trailing whitespace, EOF fixer, large file check, merge conflict detection, no commits to main)
2. **ruff** (linter) — runs `ruff check --fix` on all files
3. **ruff-format** — runs `ruff format` on all files
4. **bandit** — SAST scan of `pyresults/` source code (`-ll`, skipping B101)
5. **yamllint** — YAML syntax and formatting validation (`--strict`)
6. **actionlint** — GitHub Actions workflow static analysis
7. **ty** — runs `uv run ty check` for type checking

All code must pass these checks before committing. Run them with:
```bash
uv run pre-commit run --all-files
```

### Ruff Configuration (pyproject.toml)
- **Line length**: 100 characters max
- **Target version**: py310
- **Enabled lint rules**: E (pycodestyle errors), W (pycodestyle warnings), F (pyflakes), I (isort), B (flake8-bugbear), C4 (flake8-comprehensions), UP (pyupgrade)
- **Format**: double quotes, space indentation

### ty Configuration
- Type checker from Astral (not mypy)
- Configured in `[tool.ty.analysis]` in pyproject.toml
- All imports must be resolvable (`allowed-unresolved-imports = []`)

## Project Structure
```
pyresults/
├── pyresults/                  # Main package
│   ├── __main__.py             # Entry point with CLI argument parsing
│   ├── __about__.py            # Version info
│   ├── results_processor.py    # Application orchestrator
│   ├── logging_config.py       # Logging setup
│   ├── config/                 # Configuration management
│   │   ├── category_config.py  # Category definitions and rules
│   │   └── competition_config.py # Competition-wide settings
│   ├── domain/                 # Domain models (entities)
│   │   ├── athlete.py          # Athlete entity
│   │   ├── category.py         # Category entity with CategoryType enum
│   │   ├── race_result.py      # RaceResult entity
│   │   ├── round.py            # Round entity
│   │   ├── score.py            # Score entity with calculation logic
│   │   └── team.py             # Team entity with scoring logic
│   ├── repositories/           # Data access layer
│   │   ├── interfaces.py       # IRaceResultRepository, IScoreRepository ABCs
│   │   ├── csv_race_result_repository.py
│   │   └── csv_score_repository.py
│   ├── services/               # Business logic layer
│   │   ├── race_processor_service.py    # Raw race file processing
│   │   ├── individual_score_service.py  # Individual score aggregation
│   │   ├── team_score_service.py        # Team score aggregation
│   │   └── team_scoring_service.py      # Team calculation from race results
│   └── output/                 # Output generation layer
│       ├── interfaces.py       # IOutputGenerator ABC
│       ├── score_data_provider.py # Shared data provider for output
│       ├── excel_output_generator.py
│       └── pdf_output_generator.py
├── input_data/                 # Input CSV files organized by round (r1, r2, etc.)
├── data/                       # Processed output data
│   ├── r1/, r2/, etc.          # Processed results per round
│   └── scores/                 # Cumulative standings and team scores
├── tests/                      # Test files
└── pyproject.toml              # Project configuration and dependencies
```

## Key Architecture Patterns

### Data Flow
1. **Input**: CSV files in `input_data/{round}/` containing race results
2. **Processing**:
   - `ResultsProcessor` orchestrates the pipeline
   - `RaceProcessorService` normalises and cleans raw race CSV data
   - `IndividualScoreService` aggregates individual scores across rounds
   - `TeamScoringService` calculates team results from race results
   - `TeamScoreService` aggregates team scores across rounds
3. **Output**:
   - Processed CSVs in `data/`
   - `ScoreDataProvider` loads and formats score data for display
   - `ExcelOutputGenerator` and `PdfOutputGenerator` both consume `ScoreDataProvider`
