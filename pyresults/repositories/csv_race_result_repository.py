"""CSV implementation of race result repository."""

import logging
from pathlib import Path

import pandas as pd

from pyresults.domain import Athlete, DomainRaceResult

from .interfaces import IRaceResultRepository

logger = logging.getLogger(__name__)


class CsvRaceResultRepository(IRaceResultRepository):
    """Repository for loading and saving race results from/to CSV files.

    This is a concrete implementation of IRaceResultRepository that uses
    CSV files for storage, following the Dependency Inversion Principle.
    """

    def __init__(self, base_path: Path):
        """Initialize repository with base data path.

        Args:
            base_path: Base directory containing data folders (e.g., ./data)
        """
        self.base_path = base_path

    def load_race_result(self, race_name: str, round_number: str) -> DomainRaceResult | None:
        """Load a race result from CSV file.

        Args:
            race_name: Name of the race (e.g., "Men", "U13")
            round_number: Round identifier (e.g., "r1", "r2")

        Returns:
            RaceResult if file exists and can be loaded, None otherwise
        """
        file_path = self._get_file_path(race_name, round_number)

        if not file_path.exists():
            logger.warning(f"Race result file not found: {file_path}")
            return None

        logger.debug(f"Loading race result from {file_path}")
        try:
            df = pd.read_csv(file_path)
            race_result = DomainRaceResult(race_name=race_name, round_number=round_number)

            for _, row in df.iterrows():
                athlete = Athlete(
                    name=row["Name"],
                    club=row["Club"],
                    race_number=str(row["Race No"]),
                    position=int(row["Pos"]),
                    time=pd.to_timedelta(row["Time"]),
                    gender=row["Gender"],
                    category=row["Category"],
                )
                race_result.add_athlete(athlete)

            logger.info(
                f"Successfully loaded {len(race_result.athletes)} athletes from {file_path}"
            )
            return race_result
        except Exception as e:
            logger.error(f"Failed to load race result from {file_path}: {e}")
            raise OSError(f"Failed to load race result from {file_path}: {e}")

    def save_race_result(self, race_result: DomainRaceResult) -> None:
        """Save a race result to CSV file.

        Args:
            race_result: The race result to save
        """
        file_path = self._get_file_path(race_result.race_name, race_result.round_number)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Saving race result to {file_path}")

        # Convert domain objects to DataFrame
        data = []
        for athlete in race_result.athletes:
            data.append(
                {
                    "Pos": athlete.position,
                    "Race No": athlete.race_number,
                    "Name": athlete.name,
                    "Club": athlete.club,
                    "Gender": athlete.gender,
                    "Category": athlete.category,
                    "Time": athlete.time,
                }
            )

        df = pd.DataFrame(data)
        try:
            df.to_csv(file_path, index=False)
            logger.info(f"Successfully saved {len(race_result.athletes)} athletes to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save race result to {file_path}: {e}")
            raise OSError(f"Failed to save race result to {file_path}: {e}")

    def exists(self, race_name: str, round_number: str) -> bool:
        """Check if a race result exists.

        Args:
            race_name: Name of the race
            round_number: Round identifier

        Returns:
            True if CSV file exists, False otherwise
        """
        file_path = self._get_file_path(race_name, round_number)
        return file_path.exists()

    def get_available_races(self, round_number: str) -> list[str]:
        """Get list of available race names for a given round.

        Args:
            round_number: Round identifier

        Returns:
            List of race names (file stems)
        """
        round_dir = self.base_path / round_number
        if not round_dir.exists():
            logger.warning(f"Round directory not found: {round_dir}")
            return []

        # Get all CSV files in the round directory (excluding teams subdirectory)
        race_files = [f.stem for f in round_dir.glob("*.csv")]
        logger.debug(f"Found {len(race_files)} race files in {round_dir}")
        return race_files

    def _get_file_path(self, race_name: str, round_number: str) -> Path:
        """Get file path for a race result.

        Args:
            race_name: Name of the race
            round_number: Round identifier

        Returns:
            Path to the CSV file
        """
        return self.base_path / round_number / f"{race_name}.csv"
