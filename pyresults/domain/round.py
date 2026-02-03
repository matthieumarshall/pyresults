"""Round domain entity."""

from dataclasses import dataclass, field

from .race_result import RaceResult


@dataclass
class Round:
    """Represents a round of competition containing multiple races.

    A round is a collection of races that take place together
    (e.g., all age groups racing on the same day).
    """

    number: str  # e.g., "r1", "r2"
    race_results: list[RaceResult] = field(default_factory=list)

    def __post_init__(self):
        """Validate round data."""
        if not self.number:
            raise ValueError("Round number cannot be empty")

    def add_race_result(self, race_result: RaceResult) -> None:
        """Add a race result to this round."""
        if race_result.round_number != self.number:
            raise ValueError(
                f"Race result round '{race_result.round_number}' does not match "
                f"round number '{self.number}'"
            )
        self.race_results.append(race_result)

    def get_race_result(self, race_name: str) -> RaceResult:
        """Get a specific race result by name."""
        for race_result in self.race_results:
            if race_result.race_name == race_name:
                return race_result
        raise ValueError(f"Race '{race_name}' not found in round {self.number}")

    def has_race(self, race_name: str) -> bool:
        """Check if this round contains a specific race."""
        return any(rr.race_name == race_name for rr in self.race_results)

    def __len__(self) -> int:
        """Return number of races in this round."""
        return len(self.race_results)

    def __str__(self) -> str:
        return f"Round {self.number} ({len(self.race_results)} races)"

    def __repr__(self) -> str:
        return f"Round(number='{self.number}', races={len(self.race_results)})"
