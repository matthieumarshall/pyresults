"""Score data provider for output generators.

This module provides a single source of display-ready score data for all
output generators (Excel, PDF, etc.), ensuring that scoring logic stays
in the services/repositories layer and output generators only handle
rendering.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pyresults.config import CompetitionConfig

logger = logging.getLogger(__name__)


# Display-friendly column name mappings
_ROUND_DISPLAY_NAMES = {
    "r1": "R 1",
    "r2": "R 2",
    "r3": "R 3",
    "r4": "R 4",
    "r5": "R 5",
}

# Team category codes to readable titles
_TEAM_TITLES = {
    "U9B": "U9 Boys Teams",
    "U9G": "U9 Girls Teams",
    "U11B": "U11 Boys Teams",
    "U11G": "U11 Girls Teams",
    "U13B": "U13 Boys Teams",
    "U13G": "U13 Girls Teams",
    "U15B": "U15 Boys Teams",
    "U15G": "U15 Girls Teams",
    "U17M": "U17 Men's Teams",
    "U17W": "U17 Women's Teams",
    "Men": "Men's Teams",
    "Women": "Women's Teams",
}


@dataclass
class CategoryDisplayData:
    """Display-ready data for a single category."""

    category_code: str
    title: str
    dataframe: pd.DataFrame
    is_team: bool
    division: int | None = None


class ScoreDataProvider:
    """Provides display-ready score data for output generators.

    This class is the single point of contact between the persisted score
    data (CSV files produced by the scoring services) and the output layer.
    It handles:
    - Determining which categories to include (and in what order)
    - Loading raw score CSVs
    - Cleaning and formatting columns for display
    - Adding position numbers

    It does NOT contain any scoring or aggregation logic—those
    responsibilities belong exclusively to the services layer.
    """

    def __init__(self, config: CompetitionConfig):
        """Initialise provider with competition configuration.

        Args:
            config: Competition configuration
        """
        self.config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all_category_data(self) -> list[CategoryDisplayData]:
        """Return display-ready data for every category in display order.

        Returns:
            Ordered list of ``CategoryDisplayData`` objects.
        """
        results: list[CategoryDisplayData] = []

        for category_code in self._get_ordered_categories():
            # Adult team categories are split into per-division tables
            if category_code in ("Team Men", "Team Women"):
                division_data = self._get_team_division_data(category_code)
                results.extend(division_data)
            else:
                data = self.get_category_data(category_code)
                if data is not None:
                    results.append(data)

        return results

    def get_category_data(self, category_code: str) -> CategoryDisplayData | None:
        """Load and prepare display data for a single category.

        Args:
            category_code: Category code, optionally prefixed with ``"Team "``
                           for team categories.

        Returns:
            ``CategoryDisplayData`` or ``None`` if the score file does not exist.
        """
        is_team = category_code.startswith("Team ")
        csv_path = self._csv_path_for(category_code)

        if not csv_path.exists():
            return None

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read score CSV {csv_path}: {e}")
            return None

        # Determine the human-readable title
        title = self._resolve_title(category_code, is_team)

        # Clean up the DataFrame for display
        df = self._prepare_dataframe(df)

        return CategoryDisplayData(
            category_code=category_code,
            title=title,
            dataframe=df,
            is_team=is_team,
        )

    # ------------------------------------------------------------------
    # Category ordering
    # ------------------------------------------------------------------

    def _get_ordered_categories(self) -> list[str]:
        """Return all category codes in the desired display order.

        Youth individual + team pairs first, then senior/vet individual
        categories, then adult teams, then overall standings.
        """
        scores_dir = self.config.data_base_path / "scores"
        teams_dir = scores_dir / "teams"

        youth_pairs = [
            ("U9G", "U9G"),
            ("U9B", "U9B"),
            ("U11G", "U11G"),
            ("U11B", "U11B"),
            ("U13G", "U13G"),
            ("U13B", "U13B"),
            ("U15G", "U15G"),
            ("U15B", "U15B"),
            ("U17W", "U17W"),
            ("U17M", "U17M"),
        ]

        senior_codes = [
            "U20W",
            "SW",
            "WV40",
            "WV50",
            "WV60",
            "WV70",
            "U20M",
            "SM",
            "MV40",
            "MV50",
            "MV60",
            "MV70",
        ]

        adult_team_codes = ["Women", "Men"]

        overall_codes = ["WomensOverall", "MensOverall"]

        categories: list[str] = []

        # Youth: individual then team
        for individual_code, team_code in youth_pairs:
            if (scores_dir / f"{individual_code}.csv").exists():
                categories.append(individual_code)
            if teams_dir.exists() and (teams_dir / f"{team_code}.csv").exists():
                categories.append(f"Team {team_code}")

        # Senior / vet individual
        for code in senior_codes:
            if (scores_dir / f"{code}.csv").exists():
                categories.append(code)

        # Adult teams
        if teams_dir.exists():
            for code in adult_team_codes:
                if (teams_dir / f"{code}.csv").exists():
                    categories.append(f"Team {code}")

        # Overall
        for code in overall_codes:
            if (scores_dir / f"{code}.csv").exists():
                categories.append(code)

        return categories

    # ------------------------------------------------------------------
    # DataFrame preparation (display-only; no scoring logic)
    # ------------------------------------------------------------------

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and format a score DataFrame for display.

        Steps performed:
        1. Filter out rows with no name/team identifier.
        2. Rename round columns (r1 → R 1).
        3. Drop round columns that contain no data.
        4. Rename ``score`` → ``Score``.
        5. Convert numeric values to integers for clean display.
        6. Add a ``Pos`` column at the start.
        """
        # 1. Remove empty rows
        if "Name" in df.columns:
            df = df[df["Name"].notna()].copy()
        elif "Team" in df.columns:
            df = df[df["Team"].notna()].copy()

        # 2 & 3. Rename round columns and drop empty ones
        rounds_present: list[str] = []
        for raw_name, display_name in _ROUND_DISPLAY_NAMES.items():
            if raw_name not in df.columns:
                continue
            normalized = df[raw_name].replace(r"^\s*$", pd.NA, regex=True)
            if normalized.notna().any():
                df = df.rename(columns={raw_name: display_name})
                # Convert to numeric and then to nullable int for clean display
                df[display_name] = pd.to_numeric(df[display_name], errors="coerce")
                rounds_present.append(display_name)
            else:
                df = df.drop(columns=[raw_name])

        # 4. Rename score → Score
        if "score" in df.columns:
            df = df.rename(columns={"score": "Score"})
            df["Score"] = pd.to_numeric(df["Score"], errors="coerce")

        # 5. Convert float columns to nullable integers for clean display
        for col in rounds_present + (["Score"] if "Score" in df.columns else []):
            df[col] = df[col].apply(lambda x: "" if pd.isna(x) else int(x))

        # 6. Add position column
        df.insert(0, "Pos", pd.Series(range(1, len(df) + 1), dtype=int))

        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Division splitting for adult team categories
    # ------------------------------------------------------------------

    def _get_team_division_data(self, category_code: str) -> list[CategoryDisplayData]:
        """Split an adult team category into per-division tables.

        Args:
            category_code: Must be ``"Team Men"`` or ``"Team Women"``.

        Returns:
            List of ``CategoryDisplayData`` objects, one per division that
            has at least one team.
        """
        csv_path = self._csv_path_for(category_code)
        if not csv_path.exists():
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read score CSV {csv_path}: {e}")
            return []

        actual_code = category_code.removeprefix("Team ")
        if actual_code == "Men":
            division_map = self.config.mens_divisions
            base_title = "Men's Teams"
        else:
            division_map = self.config.womens_divisions
            base_title = "Women's Teams"

        # Assign each team row to a division (default 3).
        # Team names include a suffix like " A", " B" etc. — strip it to get
        # the base club name used as key in the division map.
        df["_division"] = df["Team"].map(
            lambda t: int(division_map.get(self._base_club_name(t), "3"))
        )

        results: list[CategoryDisplayData] = []
        for div in [1, 2, 3]:
            div_df = df[df["_division"] == div].copy()
            if div_df.empty:
                continue
            div_df = div_df.drop(columns=["_division"])
            div_df = self._prepare_dataframe(div_df)

            title = f"{base_title} - Division {div}"
            results.append(
                CategoryDisplayData(
                    category_code=category_code,
                    title=title,
                    dataframe=div_df,
                    is_team=True,
                    division=div,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _base_club_name(team_name: str) -> str:
        """Strip the team suffix (e.g. ' A', ' B') from a team name.

        Returns the base club name used as key in division maps.
        """
        import re

        return re.sub(r"\s+[A-Z]$", "", team_name)

    def _csv_path_for(self, category_code: str) -> Path:
        """Resolve the CSV file path for a category code."""
        scores_dir = self.config.data_base_path / "scores"
        if category_code.startswith("Team "):
            actual = category_code.removeprefix("Team ")
            return scores_dir / "teams" / f"{actual}.csv"
        return scores_dir / f"{category_code}.csv"

    def _resolve_title(self, category_code: str, is_team: bool) -> str:
        """Resolve a human-readable title for a category."""
        if is_team:
            actual = category_code.removeprefix("Team ")
            return _TEAM_TITLES.get(actual, f"Team {actual}")

        try:
            category = self.config.category_config.get_category(category_code)
            return category.name
        except (ValueError, KeyError) as e:
            logger.warning(
                f"Could not find category name for {category_code}, using code as title: {e}"
            )
            return category_code
