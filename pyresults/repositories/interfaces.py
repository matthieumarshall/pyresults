"""Repository interfaces (abstract base classes).

These interfaces define contracts for data access, allowing
different implementations (CSV, database, API, etc.) without
changing business logic.
"""

from abc import ABC, abstractmethod

from pyresults.domain import DomainRaceResult, Score


class IRaceResultRepository(ABC):
    """Abstract repository for race result data access."""

    @abstractmethod
    def load_race_result(self, race_name: str, round_number: str) -> DomainRaceResult | None:
        """Load a race result from storage.

        Args:
            race_name: Name of the race (e.g., "Men", "U13")
            round_number: Round identifier (e.g., "r1", "r2")

        Returns:
            RaceResult if found, None otherwise
        """
        pass

    @abstractmethod
    def save_race_result(self, race_result: DomainRaceResult) -> None:
        """Save a race result to storage.

        Args:
            race_result: The race result to save
        """
        pass

    @abstractmethod
    def exists(self, race_name: str, round_number: str) -> bool:
        """Check if a race result exists in storage.

        Args:
            race_name: Name of the race
            round_number: Round identifier

        Returns:
            True if race result exists, False otherwise
        """
        pass

    @abstractmethod
    def get_available_races(self, round_number: str) -> list[str]:
        """Get list of available race names for a given round.

        Args:
            round_number: Round identifier

        Returns:
            List of race names
        """
        pass


class IScoreRepository(ABC):
    """Abstract repository for score data access."""

    @abstractmethod
    def load_scores(self, category: str) -> list[Score]:
        """Load all scores for a category.

        Args:
            category: Category code (e.g., "U13B", "MV40")

        Returns:
            List of Score objects
        """
        pass

    @abstractmethod
    def save_scores(self, category: str, scores: list[Score]) -> None:
        """Save scores for a category.

        Args:
            category: Category code
            scores: List of Score objects to save
        """
        pass

    @abstractmethod
    def exists(self, category: str) -> bool:
        """Check if scores exist for a category.

        Args:
            category: Category code

        Returns:
            True if scores exist, False otherwise
        """
        pass


class ITeamResultRepository(ABC):
    """Abstract repository for per-round team result data access.

    Stores the intermediate team result rows that are produced after each round
    is processed (team name, position, score) and consumed by TeamScoreService
    when aggregating standings across rounds.
    """

    @abstractmethod
    def load_team_results(self, category_code: str, round_number: str) -> list[dict]:
        """Load team result rows for a category and round.

        Args:
            category_code: Category code (e.g., "U13B", "Men")
            round_number: Round identifier (e.g., "r1", "r2")

        Returns:
            List of dicts with at minimum "team" and "pos" keys; optionally "score".
        """
        pass

    @abstractmethod
    def save_team_results(
        self, category_code: str, round_number: str, data: list[dict]
    ) -> None:
        """Save team result rows for a category and round.

        Args:
            category_code: Category code
            round_number: Round identifier
            data: List of dicts representing team result rows
        """
        pass

    @abstractmethod
    def team_results_exist(self, category_code: str, round_number: str) -> bool:
        """Check if team results exist for a category and round.

        Args:
            category_code: Category code
            round_number: Round identifier

        Returns:
            True if team results exist, False otherwise
        """
        pass
