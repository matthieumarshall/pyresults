"""Athlete domain entity."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Athlete:
    """Represents an individual athlete in a race.

    This is a domain entity that encapsulates athlete data and behavior,
    replacing the primitive obsession of passing around dictionaries and DataFrames.
    """

    name: str
    club: str
    race_number: str
    position: int
    time: timedelta
    gender: str
    category: str

    def __post_init__(self):
        """Validate athlete data."""
        if not self.name:
            raise ValueError("Athlete name cannot be empty")
        if not self.club:
            raise ValueError("Athlete club cannot be empty")
        if self.position < 1:
            raise ValueError(f"Position must be positive, got {self.position}")

    def is_guest(self, guest_numbers: set[str]) -> bool:
        """Check if this athlete is a guest (not eligible for scoring)."""
        return self.race_number in guest_numbers

    def __str__(self) -> str:
        return f"{self.name} ({self.club})"

    def __repr__(self) -> str:
        return f"Athlete(name='{self.name}', club='{self.club}', position={self.position})"
