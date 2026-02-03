"""Race processor service for loading and processing race results."""

import logging
from pathlib import Path

import pandas as pd

from pyresults.config import CompetitionConfig
from pyresults.domain import Athlete, DomainRaceResult
from pyresults.repositories import IRaceResultRepository

logger = logging.getLogger(__name__)


class RaceProcessorService:
    """Service for processing raw race result files into domain objects.

    This service handles:
    - Reading race result CSV files
    - Cleaning and normalizing data
    - Filtering guests
    - Applying race-specific exceptions
    - Creating domain objects
    - Persisting processed results

    This replaces the old RaceResult class's constructor logic,
    separating data loading from business logic.
    """

    def __init__(self, config: CompetitionConfig, repository: IRaceResultRepository):
        """Initialize service with dependencies.

        Args:
            config: Competition configuration
            repository: Repository for saving processed results
        """
        self.config = config
        self.repository = repository

    def process_race_file(self, file_path: Path) -> DomainRaceResult:
        """Process a race result file into a domain object.

        Args:
            file_path: Path to the CSV file containing race results

        Returns:
            DomainRaceResult object with processed data
        """
        race_name = file_path.stem
        round_number = file_path.parent.name

        logger.info(f"Processing race file: {race_name} for {round_number}")

        # Load and clean data
        df = self._read_race_file(file_path)
        df = self._clean_data(df, race_name, round_number)

        # Create domain object
        race_result = DomainRaceResult(race_name=race_name, round_number=round_number)

        # Convert DataFrame rows to Athlete objects
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

        return race_result

    def process_and_save(self, file_path: Path) -> DomainRaceResult:
        """Process a race file and save the results.

        Args:
            file_path: Path to the race result file

        Returns:
            Processed race result
        """
        race_result = self.process_race_file(file_path)
        self.repository.save_race_result(race_result)
        return race_result

    def _read_race_file(self, file_path: Path) -> pd.DataFrame:
        """Read race result CSV file.

        Tries UTF-16 encoding with both comma and tab separators.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame containing race results
        """
        try:
            df = pd.read_csv(file_path, encoding="utf-16")
            df["Race No"]  # Verify column exists
            logger.debug(f"Successfully read {file_path} with UTF-16 encoding (comma separator)")
            return df
        except (KeyError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to read with UTF-16 comma separator, trying tab separator: {e}")
            df = pd.read_csv(file_path, encoding="utf-16", sep="\t")
            logger.debug(f"Successfully read {file_path} with UTF-16 encoding (tab separator)")
            return df

    def _clean_data(self, df: pd.DataFrame, race_name: str, round_number: str) -> pd.DataFrame:
        """Clean and normalize race data.

        Args:
            df: Raw DataFrame
            race_name: Name of the race
            round_number: Round identifier

        Returns:
            Cleaned DataFrame
        """
        # Normalize names
        df["Name"] = df["Name"].apply(self._clean_name)

        # Convert data types
        df["Race No"] = df["Race No"].astype(str)
        df["Pos"] = pd.to_numeric(df["Pos"], errors="coerce")
        df["Time"] = pd.to_timedelta(df["Time"])

        # Filter guests
        initial_count = len(df)
        df = df[~df["Race No"].isin(self.config.guest_numbers)]
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            logger.debug(f"Filtered {filtered_count} guest entries from {race_name}")

        # Reset positions after filtering
        df = self._reset_positions(df)

        # Apply race/round-specific exceptions
        df = self._handle_exceptions(df, race_name, round_number)

        # Map categories
        df = self._map_categories(df, race_name)

        return df

    def _clean_name(self, name: str) -> str:
        """Clean and normalize athlete name.

        Args:
            name: Raw name string

        Returns:
            Cleaned name
        """
        if pd.isna(name):
            return ""
        # Convert to string and strip whitespace
        name = str(name).strip()
        # Remove extra spaces
        name = " ".join(name.split())
        return name

    def _reset_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset position numbers sequentially after filtering.

        Args:
            df: DataFrame with potentially non-sequential positions

        Returns:
            DataFrame with sequential positions
        """
        df = df.sort_values("Pos").reset_index(drop=True)
        df["Pos"] = range(1, len(df) + 1)
        return df

    def _handle_exceptions(
        self, df: pd.DataFrame, race_name: str, round_number: str
    ) -> pd.DataFrame:
        """Handle race/round-specific exceptions and corrections.

        This method can be extended to handle specific data issues or corrections
        for particular races and rounds.

        Args:
            df: DataFrame to apply exceptions to
            race_name: Name of the race
            round_number: Round identifier

        Returns:
            DataFrame with exceptions applied
        """
        # Example: Handle specific exceptions for certain races/rounds
        # This can be expanded based on the original handle_exceptions logic
        return df

    def _map_categories(self, df: pd.DataFrame, race_name: str) -> pd.DataFrame:
        """Map race categories to standard category codes and add Gender column.

        Args:
            df: DataFrame with race data
            race_name: Name of the race

        Returns:
            DataFrame with Gender and Category columns added
        """
        # First, add Gender column based on race name or existing data
        if "Gender" not in df.columns:
            try:
                # Try to get gender from race name
                default_gender = self.config.get_gender_for_race(race_name)
                df["Gender"] = default_gender
            except (ValueError, KeyError):
                # Default to Male if we can't determine gender
                df["Gender"] = "Male"

        # Now map categories
        def map_row(row):
            try:
                # Get gender from the row (now it exists)
                gender = row["Gender"]
                # Get race category from row or use race name
                if "Race Category" in df.columns:
                    race_category = row["Race Category"]
                elif "Category" in df.columns and pd.notna(row.get("Category")):
                    race_category = row["Category"]
                else:
                    race_category = race_name

                # Map to standard category code
                return self.config.map_category(gender, race_category)
            except (ValueError, KeyError) as e:
                # If no mapping found, return empty string
                logger.warning(f"Failed to map category for {race_name}: {e}")
                return ""

        df["Category"] = df.apply(map_row, axis=1)
        return df
