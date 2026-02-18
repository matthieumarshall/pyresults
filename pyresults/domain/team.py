"""Team domain entity."""

import math
from dataclasses import dataclass, field

from .athlete import Athlete


@dataclass
class Team:
    """Represents a team of athletes competing together.

    Encapsulates team scoring logic and team composition rules.
    """

    club: str
    category: str
    label: str = "A"  # Team label: A, B, C, etc.
    athletes: list[Athlete] = field(default_factory=list)

    def __post_init__(self):
        """Validate team data."""
        if not self.club:
            raise ValueError("Team club cannot be empty")
        if not self.category:
            raise ValueError("Team category cannot be empty")
        if not self.label:
            raise ValueError("Team label cannot be empty")

    @property
    def name(self) -> str:
        """Get full team name with label (e.g., 'Oxford AC A')."""
        return f"{self.club} {self.label}"

    def add_athlete(self, athlete: Athlete) -> None:
        """Add an athlete to the team."""
        if athlete.club != self.club:
            raise ValueError(
                f"Athlete {athlete.name} club '{athlete.club}' does not match "
                f"team club '{self.club}'"
            )
        self.athletes.append(athlete)

    def calculate_score(self, team_size: int, penalty_score: int) -> int:
        """Calculate team score as sum of positions of top N athletes.

        Args:
            team_size: Number of athletes that count towards score
            penalty_score: Penalty score for missing athletes (n+1 where n is total in category)

        Returns:
            Team score (sum of positions), with penalty for incomplete teams
        """
        min_team_size = math.ceil(team_size / 2)
        
        if len(self.athletes) < min_team_size:
            return 999999  # Team too small to be valid

        # Sort by position and take top N (or all if less than team_size)
        scoring_athletes = sorted(self.athletes, key=lambda a: a.position)[:team_size]
        score = sum(athlete.position for athlete in scoring_athletes)
        
        # Add penalty for missing athletes
        missing_count = team_size - len(self.athletes)
        if missing_count > 0:
            score += missing_count * penalty_score
        
        return score

    def is_complete(self, team_size: int) -> bool:
        """Check if team has enough athletes to score."""
        min_team_size = math.ceil(team_size / 2)
        return len(self.athletes) >= min_team_size

    def get_scoring_athletes(self, team_size: int) -> list[Athlete]:
        """Get the athletes that count towards the team score."""
        if not self.is_complete(team_size):
            return []
        return sorted(self.athletes, key=lambda a: a.position)[:team_size]

    def __str__(self) -> str:
        return f"{self.name} {self.category} ({len(self.athletes)} athletes)"

    def __repr__(self) -> str:
        return (
            f"Team(club='{self.club}', label='{self.label}', category='{self.category}', athletes={len(self.athletes)})"
        )
