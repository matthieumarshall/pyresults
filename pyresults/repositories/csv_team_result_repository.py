"""CSV implementation of the team result repository."""

import logging
from pathlib import Path

from .interfaces import ITeamResultRepository

logger = logging.getLogger(__name__)


class CsvTeamResultRepository(ITeamResultRepository):
    """Repository for loading and saving per-round team results from/to CSV files.

    Files are stored at:
        <base_path>/<round_number>/teams/<category_code>.csv

    Each CSV row represents one team and contains at minimum the columns
    ``team``, ``pos``, and optionally ``score``.
    """

    def __init__(self, base_path: Path):
        """Initialize repository.

        Args:
            base_path: Base data directory (e.g., ./data).  Round sub-directories
                are resolved relative to this path.
        """
        try:
            import pandas as pd  # noqa: F401 – validate availability at construction
        except ImportError as exc:
            raise ImportError(
                "pandas is required for CsvTeamResultRepository. "
                "Install with: pip install 'pyresults[output]'"
            ) from exc

        self.base_path = base_path

    # ------------------------------------------------------------------
    # ITeamResultRepository implementation
    # ------------------------------------------------------------------

    def load_team_results(self, category_code: str, round_number: str) -> list[dict]:
        """Load team result rows from the CSV for a category and round.

        Args:
            category_code: Category code (e.g., ``"U13B"``, ``"Men"``)
            round_number: Round identifier (e.g., ``"r1"``)

        Returns:
            List of dicts representing team result rows.  Each dict normalises
            column names to lower-case and always includes at least ``"team"``
            and ``"pos"`` keys.
        """
        import pandas as pd

        file_path = self._get_path(category_code, round_number)

        if not file_path.exists():
            logger.debug(f"No team results file for {category_code}/{round_number}: {file_path}")
            return []

        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.lower()
            return df.to_dict(orient="records")
        except Exception as exc:
            logger.error(f"Failed to read team results from {file_path}: {exc}")
            raise OSError(f"Failed to read team results from {file_path}: {exc}") from exc

    def save_team_results(self, category_code: str, round_number: str, data: list[dict]) -> None:
        """Save team result rows to CSV.

        Args:
            category_code: Category code
            round_number: Round identifier
            data: List of dicts representing team result rows
        """
        import pandas as pd

        if not data:
            return

        file_path = self._get_path(category_code, round_number)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        logger.debug(f"Saved {len(data)} team result rows to {file_path}")

    def team_results_exist(self, category_code: str, round_number: str) -> bool:
        """Return True if a team results file exists for the given category and round."""
        return self._get_path(category_code, round_number).exists()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_path(self, category_code: str, round_number: str) -> Path:
        return self.base_path / round_number / "teams" / f"{category_code}.csv"
