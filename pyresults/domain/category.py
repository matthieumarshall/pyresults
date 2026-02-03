"""Category domain entity and related enums."""

from dataclasses import dataclass
from enum import Enum


class CategoryType(Enum):
    """Type of competition category."""

    TEAM = "team"
    INDIVIDUAL = "individual"
    OVERALL = "overall"  # Combined categories (e.g., all men's categories)


class Gender(Enum):
    """Gender classification."""

    MALE = "Male"
    FEMALE = "Female"


@dataclass
class Category:
    """Represents a competition category with its rules and configuration.

    Encapsulates category-specific business rules, replacing hard-coded
    dictionaries and scattered conditional logic.
    """

    code: str  # e.g., "U13B", "MV40", "SM"
    name: str  # e.g., "Under 13 Boys", "Men V40"
    category_type: CategoryType
    gender: Gender
    race_name: str  # The race file this category appears in (e.g., "U13", "Men")
    team_size: int | None = None  # Number of athletes per team (for team categories)
    age_group: str | None = None  # e.g., "U13", "V40", "Senior"

    def __post_init__(self):
        """Validate category configuration."""
        if not self.code:
            raise ValueError("Category code cannot be empty")
        if not self.name:
            raise ValueError("Category name cannot be empty")
        if self.category_type == CategoryType.TEAM:
            if self.team_size is None:
                raise ValueError(f"Team category {self.code} must have team_size defined")
            if self.team_size < 1:
                raise ValueError(f"Team size must be positive, got {self.team_size}")

    def is_team_category(self) -> bool:
        """Check if this is a team category."""
        return self.category_type == CategoryType.TEAM

    def is_individual_category(self) -> bool:
        """Check if this is an individual category."""
        return self.category_type == CategoryType.INDIVIDUAL

    def is_overall_category(self) -> bool:
        """Check if this is an overall category."""
        return self.category_type == CategoryType.OVERALL

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"Category(code='{self.code}', type={self.category_type.value})"
