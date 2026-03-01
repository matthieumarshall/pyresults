# pyresults

A Python library for calculating and publishing standings for the **Oxfordshire Cross Country League**. It processes raw race result CSV files exported from a timing system, computes individual and team scores across multiple rounds of the season, and generates formatted Excel and PDF outputs.

---

## Features

- Processes race result CSVs for multiple age/gender categories (U9 through Senior and Veterans)
- Ranks athletes individually within their category across all completed rounds
- Calculates team scores per round and aggregates them across the season
- Supports configurable club aliases, guest runners, and divisional splits
- Generates polished **Excel** and **PDF** output files
- Clean, testable architecture following SOLID principles

---

## Setup

### Prerequisites

- Python 3.10–3.11
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Install uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone and install dependencies

```bash
git clone https://github.com/matthieumarshall/pyresults.git
cd pyresults
uv sync --all-extras
```

---

## Input data

Place race result CSV files under `data/<round>/`, one file per race category. Each CSV must contain the following columns (as exported by the timing system):

```
Pos, Race No, Name, Time, Category, Cat Pos, Gender, Gen Pos, Club
```

Example directory layout for a five-round season:

```
data/
+-- r1/
¦   +-- Men.csv
¦   +-- Women.csv
¦   +-- U9.csv
¦   +-- U11.csv
¦   +-- U13.csv
¦   +-- U15.csv
¦   +-- U17.csv
+-- r2/
¦   +-- ...
+-- scores/          # written by the tool; do not edit manually
```

---

## Usage

### Command line

Run the module directly with `uv run`:

```bash
# Process all five rounds and generate both Excel and PDF output
uv run python -m pyresults --rounds r1 r2 r3 r4 r5 --excel --pdf

# Process only the first two rounds, Excel output only
uv run python -m pyresults --rounds r1 r2 --excel

# Adjust log verbosity
uv run python -m pyresults --rounds r1 --excel --log-level DEBUG
```

**Arguments**

| Argument | Default | Description |
|---|---|---|
| `--rounds` | `r1 r2 r3 r4 r5` | Rounds to process (space- or comma-separated) |
| `--excel` | off | Generate Excel output files |
| `--pdf` | off | Generate PDF output files |
| `--log-level` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

Output files are written to the `output/` directory.

### Python API

```python
from pyresults.config import build_default_config
from pyresults.results_processor import ResultsProcessor

config = build_default_config()
processor = ResultsProcessor(config)

processor.process_rounds(
    rounds_to_process=["r1", "r2", "r3"],
    create_excel=True,
    create_pdf=True,
)
```

See [example_usage.py](example_usage.py) for a more detailed walkthrough.

---

## Development

### Run tests

```bash
uv run python -m pytest tests/
```

Or via the Hatch helper script:

```bash
hatch run test
```

### Linting and formatting

[Ruff](https://docs.astral.sh/ruff/) and [pre-commit](https://pre-commit.com/) are used for linting and formatting. Install the hooks once after cloning:

```bash
uv run pre-commit install
```

They will then run automatically on every commit.

---

## Architecture

The library follows clean architecture / SOLID principles across five layers:

| Layer | Package | Responsibility |
|---|---|---|
| Domain | `pyresults/domain/` | Core entities: `Athlete`, `Team`, `Score`, `Category`, `RaceResult`, `Round` |
| Repositories | `pyresults/repositories/` | CSV-based data access (`CsvRaceResultRepository`, `CsvScoreRepository`) |
| Configuration | `pyresults/config/` | Injectable competition and category configuration |
| Services | `pyresults/services/` | Business logic: race processing, individual scoring, team scoring |
| Output | `pyresults/output/` | Output generation (`ExcelOutputGenerator`, `PdfOutputGenerator`) |

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.
