"""CSV implementation of score repository."""

import logging
from pathlib import Path

import pandas as pd

from pyresults.domain import Score

from .interfaces import IScoreRepository

logger = logging.getLogger(__name__)


class CsvScoreRepository(IScoreRepository):
    """Repository for loading and saving scores from/to CSV files.

    This is a concrete implementation of IScoreRepository that uses
    CSV files for storage, following the Dependency Inversion Principle.
    """

    def __init__(self, base_path: Path, round_numbers: list[str]):
        """Initialize repository with base scores path.

        Args:
            base_path: Base directory containing scores (e.g., ./data/scores)
            round_numbers: List of valid round identifiers (e.g., ["r1", "r2", ...])
        """
        self.base_path = base_path
        self.round_numbers = round_numbers

    def load_scores(self, category: str) -> list[Score]:
        """Load all scores for a category from CSV file.

        Args:
            category: Category code (e.g., "U13B", "MV40")

        Returns:
            List of Score objects
        """
        file_path = self._get_file_path(category)

        if not file_path.exists():
            logger.debug(f"Score file not found for {category}: {file_path}")
            return []

        logger.debug(f"Loading scores for {category} from {file_path}")
        try:
            df = pd.read_csv(file_path)
            scores = []

            for _, row in df.iterrows():
                round_scores = {}
                for round_num in self.round_numbers:
                    if round_num in df.columns and pd.notna(row[round_num]):
                        round_scores[round_num] = int(row[round_num])

                score = Score(
                    name=row["Name"],
                    club=row["Club"] if "Club" in df.columns else None,
                    category=category,
                    round_scores=round_scores,
                )
                scores.append(score)

            logger.info(f"Successfully loaded {len(scores)} scores for {category} from {file_path}")
            return scores
        except Exception as e:
            logger.error(f"Failed to load scores from {file_path}: {e}")
            raise OSError(f"Failed to load scores from {file_path}: {e}") from e

    def save_scores(self, category: str, scores: list[Score]) -> None:
        """Save scores for a category to CSV file.

        Args:
            category: Category code
            scores: List of Score objects to save
        """
        file_path = self._get_file_path(category)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Saving {len(scores)} scores for {category} to {file_path}")

        # League rule: total is based on best (n-1) rounds, where n is the
        # number of rounds that have data for this category.
        rounds_with_data = {
            round_num
            for score in scores
            for round_num in self.round_numbers
            if round_num in score.round_scores
        }
        rounds_available = len(rounds_with_data)
        rounds_to_count = rounds_available if rounds_available <= 1 else rounds_available - 1

        # Convert domain objects to DataFrame
        data = []
        for score in scores:
            row = {
                "Name": score.name,
                "Club": score.club if score.club else "",
            }

            # Add round scores
            for round_num in self.round_numbers:
                if round_num in score.round_scores:
                    row[round_num] = str(score.round_scores[round_num])
                else:
                    row[round_num] = ""

            # Calculate total score from best (n-1) rounds.
            total = score.calculate_total_score(rounds_to_count)
            row["score"] = "" if total > 99999 else str(total)

            data.append(row)

        df = pd.DataFrame(data)

        # Ensure columns are in correct order
        columns = ["Name", "Club"] + self.round_numbers + ["score"]
        for col in columns:
            if col not in df.columns:
                df[col] = ""

        df = df[columns]
        try:
            df.to_csv(file_path, index=False)
            logger.info(f"Successfully saved {len(scores)} scores for {category} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save scores to {file_path}: {e}")
            raise OSError(f"Failed to save scores to {file_path}: {e}") from e

    def exists(self, category: str) -> bool:
        """Check if scores exist for a category.

        Args:
            category: Category code

        Returns:
            True if CSV file exists, False otherwise
        """
        file_path = self._get_file_path(category)
        return file_path.exists()

    def _get_file_path(self, category: str) -> Path:
        """Get file path for a category's scores.

        Args:
            category: Category code

        Returns:
            Path to the CSV file
        """
        return self.base_path / f"{category}.csv"
