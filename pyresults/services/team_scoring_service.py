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
        # For adult team categories (Men/Women), use all athletes in the race
        # For junior team categories (U9B, U11G, etc.), filter by category
        if category.code in ["Men", "Women"]:
            athletes = race_result.athletes
        else:
            athletes = race_result.get_athletes_by_category(category.code)
        
        logger.debug(f"Calculating teams for {category.code}: {len(athletes)} athletes found")

        if category.team_size is None:
            raise ValueError(f"Category {category.code} has no team_size defined")
        
        team_size = category.team_size
        min_team_size = (team_size + 1) // 2  # Ceiling division: at least half
        
        # Calculate penalty score (n+1 where n is total athletes in category)
        penalty_score = len(athletes) + 1
        
        # Group athletes by club and sort by position
        from collections import defaultdict
        clubs: dict[str, list[Athlete]] = defaultdict(list)
        
        for athlete in athletes:
            clubs[athlete.club].append(athlete)
        
        # Create multiple teams per club
        teams = []
        
        for club, club_athletes in clubs.items():
            # Sort athletes by position
            club_athletes.sort(key=lambda a: a.position)
            
            # Split into multiple teams (A, B, C, etc.)
            team_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
            
            team_index = 0
            athlete_index = 0
            
            while athlete_index < len(club_athletes):
                # Create a new team
                if team_index >= len(team_labels):
                    logger.warning(f"Club {club} has more teams than available labels")
                    break
                
                label = team_labels[team_index]
                team = Team(club=club, category=category.code, label=label)
                
                # Add athletes to this team (up to team_size)
                for _ in range(team_size):
                    if athlete_index < len(club_athletes):
                        team.add_athlete(club_athletes[athlete_index])
                        athlete_index += 1
                    else:
                        break
                
                # Only include teams that meet minimum size requirement
                if len(team.athletes) >= min_team_size:
                    teams.append(team)
                else:
                    logger.debug(
                        f"Team {team.name} has only {len(team.athletes)} athletes "
                        f"(minimum {min_team_size}), excluding from results"
                    )
                
                team_index += 1
        
        # Calculate scores and sort
        teams.sort(key=lambda t: t.calculate_score(team_size, penalty_score))

        return teams

    def create_team_result_data(self, teams: list[Team], team_size: int, penalty_score: int) -> list[dict]:
        """Create team result data for output.

        Args:
            teams: List of Team objects
            team_size: Number of athletes that count towards score
            penalty_score: Penalty score for missing athletes

        Returns:
            List of dictionaries containing team result data
        """
        result_data = []

        position = 1
        for team in teams:
            score = team.calculate_score(team_size, penalty_score)

            # Only include teams with valid scores
            if score >= 999999:
                continue

            # Get scoring athletes
            scoring_athletes = team.get_scoring_athletes(team_size)

            # Create row data with team name (includes label)
            row = {"Pos": position, "Team": team.name, "Score": score}

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
