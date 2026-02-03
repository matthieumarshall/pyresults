"""Score domain entity."""

from dataclasses import dataclass


@dataclass
class Score:
    """Represents an athlete's or team's score across multiple rounds.

    Encapsulates scoring logic and cumulative score calculation.
    """

    name: str  # Athlete name or club name
    club: str | None  # Club (for individual athletes) or None (for teams)
    category: str
    round_scores: dict[str, int]  # round_number -> position/score

    def __post_init__(self):
        """Validate score data."""
        if not self.name:
            raise ValueError("Score name cannot be empty")
        if not self.category:
            raise ValueError("Score category cannot be empty")

    def add_round_score(self, round_number: str, score: int) -> None:
        """Add or update a score for a specific round."""
        if score < 1:
            raise ValueError(f"Score must be positive, got {score}")
        self.round_scores[round_number] = score

    def calculate_total_score(self, rounds_to_count: int) -> int:
        """Calculate total score based on best N rounds.

        Args:
            rounds_to_count: Number of best rounds to count towards total

        Returns:
            Total score (sum of best N rounds), or 999999 if insufficient rounds
        """
        if not self.round_scores:
            return 999999

        # Get the best (lowest) scores
        scores = sorted(self.round_scores.values())

        # Need at least rounds_to_count rounds to have a valid score
        if len(scores) < rounds_to_count:
            return 999999

        return sum(scores[:rounds_to_count])

    def get_rounds_competed(self) -> int:
        """Get number of rounds this athlete/team has competed in."""
        return len(self.round_scores)

    def __str__(self) -> str:
        total = self.calculate_total_score(len(self.round_scores))
        return f"{self.name}: {total} pts"

    def __repr__(self) -> str:
        return f"Score(name='{self.name}', category='{self.category}', rounds={len(self.round_scores)})"
