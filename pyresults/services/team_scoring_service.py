"""Team scoring service for calculating team results."""

import logging

from pyresults.config import CompetitionConfig
from pyresults.domain import Category, DomainRaceResult, Team

logger = logging.getLogger(__name__)


class TeamScoringService:
    """Service for calculating team scores from race results.

    This service handles:
    - Grouping athletes by club
    - Creating team objects
    - Calculating team scores based on team size
    - Generating team result data

    This replaces the static calculate_teams method from the old RaceResult class,
    following the Single Responsibility Principle.
    """

    def __init__(self, config: CompetitionConfig):
        """Initialize service with configuration.

        Args:
            config: Competition configuration
        """
        self.config = config

    def calculate_teams_for_race(
        self, race_result: DomainRaceResult, category: Category
    ) -> list[Team]:
        """Calculate team scores for a specific category in a race.

        Args:
            race_result: Race result containing athlete data
            category: Category to calculate teams for

        Returns:
            List of Team objects, sorted by score
        """
        if not category.is_team_category():
            raise ValueError(f"Category {category.code} is not a team category")

        # Get athletes in this category
        athletes = race_result.get_athletes_by_category(category.code)
        logger.debug(f"Calculating teams for {category.code}: {len(athletes)} athletes found")

        # Group athletes by club
        teams_dict: dict[str, Team] = {}

        for athlete in athletes:
            if athlete.club not in teams_dict:
                teams_dict[athlete.club] = Team(club=athlete.club, category=category.code)

            teams_dict[athlete.club].add_athlete(athlete)

        # Convert to list
        teams = list(teams_dict.values())

        # Calculate scores and sort
        if category.team_size is None:
            raise ValueError(f"Category {category.code} has no team_size defined")
        team_size = category.team_size
        teams.sort(key=lambda t: t.calculate_score(team_size))

        return teams

    def create_team_result_data(self, teams: list[Team], team_size: int) -> list[dict]:
        """Create team result data for output.

        Args:
            teams: List of Team objects
            team_size: Number of athletes that count towards score

        Returns:
            List of dictionaries containing team result data
        """
        result_data = []

        position = 1
        for team in teams:
            score = team.calculate_score(team_size)

            # Only include teams with valid scores
            if score >= 999999:
                continue

            # Get scoring athletes
            scoring_athletes = team.get_scoring_athletes(team_size)

            # Create row data
            row = {"Pos": position, "Club": team.club, "Score": score}

            # Add individual athlete positions
            for i, athlete in enumerate(scoring_athletes, 1):
                row[f"Runner{i}"] = f"{athlete.name} ({athlete.position})"

            result_data.append(row)
            position += 1

        return result_data

    def get_team_categories_for_race(self, race_name: str) -> list[str]:
        """Get list of team categories that apply to a given race.

        Args:
            race_name: Name of the race (e.g., "Men", "U13")

        Returns:
            List of category codes that have teams in this race
        """
        all_categories = self.config.category_config.get_all_categories()

        team_categories = []
        for category in all_categories:
            if category.is_team_category() and category.race_name == race_name:
                team_categories.append(category.code)

        return team_categories
