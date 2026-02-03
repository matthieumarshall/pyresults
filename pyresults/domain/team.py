"""Team domain entity."""

from dataclasses import dataclass, field

from .athlete import Athlete


@dataclass
class Team:
    """Represents a team of athletes competing together.

    Encapsulates team scoring logic and team composition rules.
    """

    club: str
    category: str
    athletes: list[Athlete] = field(default_factory=list)

    def __post_init__(self):
        """Validate team data."""
        if not self.club:
            raise ValueError("Team club cannot be empty")
        if not self.category:
            raise ValueError("Team category cannot be empty")

    def add_athlete(self, athlete: Athlete) -> None:
        """Add an athlete to the team."""
        if athlete.club != self.club:
            raise ValueError(
                f"Athlete {athlete.name} club '{athlete.club}' does not match "
                f"team club '{self.club}'"
            )
        self.athletes.append(athlete)

    def calculate_score(self, team_size: int) -> int:
        """Calculate team score as sum of positions of top N athletes.

        Args:
            team_size: Number of athletes that count towards score

        Returns:
            Team score (sum of positions), or 999999 if incomplete team
        """
        if len(self.athletes) < team_size:
            return 999999  # Incomplete team

        # Sort by position and take top N
        scoring_athletes = sorted(self.athletes, key=lambda a: a.position)[:team_size]
        return sum(athlete.position for athlete in scoring_athletes)

    def is_complete(self, team_size: int) -> bool:
        """Check if team has enough athletes to score."""
        return len(self.athletes) >= team_size

    def get_scoring_athletes(self, team_size: int) -> list[Athlete]:
        """Get the athletes that count towards the team score."""
        if not self.is_complete(team_size):
            return []
        return sorted(self.athletes, key=lambda a: a.position)[:team_size]

    def __str__(self) -> str:
        return f"{self.club} {self.category} ({len(self.athletes)} athletes)"

    def __repr__(self) -> str:
        return (
            f"Team(club='{self.club}', category='{self.category}', athletes={len(self.athletes)})"
        )
