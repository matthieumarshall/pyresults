"""RaceResult domain entity."""

from dataclasses import dataclass, field

from .athlete import Athlete


@dataclass
class RaceResult:
    """Represents the results of a single race.

    Encapsulates race result data and provides a clean interface for
    accessing athlete results.
    """

    race_name: str
    round_number: str
    athletes: list[Athlete] = field(default_factory=list)

    def __post_init__(self):
        """Validate race result data."""
        if not self.race_name:
            raise ValueError("Race name cannot be empty")
        if not self.round_number:
            raise ValueError("Round number cannot be empty")

    def add_athlete(self, athlete: Athlete) -> None:
        """Add an athlete result to this race."""
        self.athletes.append(athlete)

    def get_athletes_by_category(self, category: str) -> list[Athlete]:
        """Get all athletes in a specific category."""
        return [a for a in self.athletes if a.category == category]

    def get_athletes_by_club(self, club: str) -> list[Athlete]:
        """Get all athletes from a specific club."""
        return [a for a in self.athletes if a.club == club]

    def get_clubs(self) -> set[str]:
        """Get set of all clubs that competed in this race."""
        return {athlete.club for athlete in self.athletes}

    def get_categories(self) -> set[str]:
        """Get set of all categories in this race."""
        return {athlete.category for athlete in self.athletes}

    def __len__(self) -> int:
        """Return number of athletes in this race."""
        return len(self.athletes)

    def __str__(self) -> str:
        return f"{self.race_name} {self.round_number} ({len(self.athletes)} athletes)"

    def __repr__(self) -> str:
        return f"RaceResult(race='{self.race_name}', round='{self.round_number}', athletes={len(self.athletes)})"
