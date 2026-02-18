"""Individual score aggregation service."""

import logging

from pyresults.config import CompetitionConfig
from pyresults.domain import CategoryType, Score
from pyresults.repositories import IRaceResultRepository, IScoreRepository

logger = logging.getLogger(__name__)


class IndividualScoreService:
    """Service for aggregating individual athlete scores across rounds.

    This service handles:
    - Loading race results for each round
    - Building cumulative scores for each athlete
    - Calculating total scores based on best N rounds
    - Persisting updated scores

    This replaces part of the Results.update_individual_scores() logic,
    following the Single Responsibility Principle.
    """

    def __init__(
        self,
        config: CompetitionConfig,
        race_result_repo: IRaceResultRepository,
        score_repo: IScoreRepository,
    ):
        """Initialize service with dependencies.

        Args:
            config: Competition configuration
            race_result_repo: Repository for loading race results
            score_repo: Repository for loading and saving scores
        """
        self.config = config
        self.race_result_repo = race_result_repo
        self.score_repo = score_repo

    def update_scores_for_category(self, category_code: str) -> None:
        """Update scores for a specific category across all rounds.

        This method recomputes all scores from scratch using the race results.
        It does NOT preserve existing scores, as the race results are the
        source of truth and should be reprocessed each time.

        Args:
            category_code: Category code (e.g., "U13B", "MV40")
        """
        logger.info(f"Updating individual scores for category: {category_code}")

        # Get category configuration
        category = self.config.category_config.get_category(category_code)
        race_name = category.race_name

        # Start with empty score map - we recompute from race results each time
        # This ensures scores always reflect current race data
        score_map: dict[tuple[str, str], Score] = {}

        # Process each round
        rounds_processed = 0
        for round_number in self.config.round_numbers:
            if not self.race_result_repo.exists(race_name, round_number):
                logger.debug(f"No race result for {race_name} in {round_number}")
                continue

            rounds_processed += 1
            race_result = self.race_result_repo.load_race_result(race_name, round_number)

            if race_result is None:
                logger.warning(f"Failed to load race result for {race_name} in {round_number}")
                continue

            # Get athletes in this category, sorted by overall position
            # to determine category-specific position
            category_athletes = race_result.get_athletes_by_category(category_code)
            category_athletes.sort(key=lambda a: a.position)

            # Update scores for each athlete using their position within the category
            for category_position, athlete in enumerate(category_athletes, start=1):
                key = (athlete.name, athlete.club)

                if key not in score_map:
                    # Create new score entry
                    score = Score(
                        name=athlete.name,
                        club=athlete.club,
                        category=category_code,
                        round_scores={},
                    )
                    score_map[key] = score

                # Add this round's category-specific position (not overall race position)
                score_map[key].add_round_score(round_number, category_position)

        # Convert back to list
        updated_scores = list(score_map.values())

        # League rule: rank by best (n-1) rounds, where n is rounds processed.
        rounds_to_count = rounds_processed if rounds_processed <= 1 else rounds_processed - 1
        updated_scores.sort(key=lambda s: s.calculate_total_score(rounds_to_count))

        # Save updated scores
        self.score_repo.save_scores(category_code, updated_scores)
        logger.info(
            f"Saved {len(updated_scores)} scores for {category_code} "
            f"({rounds_processed} rounds processed)"
        )

    def update_all_categories(self) -> None:
        """Update scores for all individual categories.
        
        This includes:
        - INDIVIDUAL categories (adult categories like SM, MV40, etc.)
        - TEAM categories (youth categories like U9B, U9G, etc.) which also need individual scoring
        """
        individual_categories = self.config.category_config.get_categories_by_type(
            CategoryType.INDIVIDUAL
        )
        
        # Also include youth team categories which need individual scoring
        team_categories = self.config.category_config.get_categories_by_type(
            CategoryType.TEAM
        )
        # Filter to only include youth categories (exclude adult team categories like "Men", "Women")
        youth_team_categories = [
            cat for cat in team_categories 
            if cat.age_group and cat.age_group.startswith("U")
        ]

        for category in individual_categories + youth_team_categories:
            self.update_scores_for_category(category.code)

    def _load_or_create_scores(self, category_code: str) -> list[Score]:
        """Load existing scores or return empty list.

        Args:
            category_code: Category code

        Returns:
            List of existing scores or empty list
        """
        if self.score_repo.exists(category_code):
            return self.score_repo.load_scores(category_code)
        return []
