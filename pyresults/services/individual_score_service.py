"""Individual score aggregation service."""

import functools
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
        # Primary: total score (999999 for incomplete), secondary: more rounds
        # first, tertiary: lower aggregate score first.
        updated_scores.sort(
            key=lambda s: (
                s.calculate_total_score(rounds_to_count),
                -s.get_rounds_competed(),
                sum(sorted(s.round_scores.values())),
            )
        )

        # Apply head-to-head tiebreak for the top 4
        updated_scores = self._apply_head_to_head_tiebreak(updated_scores, rounds_to_count)

        # Save updated scores
        self.score_repo.save_scores(category_code, updated_scores)
        logger.info(
            f"Saved {len(updated_scores)} scores for {category_code} "
            f"({rounds_processed} rounds processed)"
        )

    def update_scores_for_overall_category(self, category_code: str) -> None:
        """Update overall scores for a race across all age groups.

        Unlike category-specific scoring, overall scoring uses each athlete's
        finishing position in the full race (not a position within their age
        category).  Every non-guest athlete in the race is included.

        Args:
            category_code: Overall category code (e.g., "MensOverall")
        """
        logger.info(f"Updating overall scores for category: {category_code}")

        category = self.config.category_config.get_category(category_code)
        race_name = category.race_name

        score_map: dict[tuple[str, str], Score] = {}

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

            # Use ALL athletes in the race, scored by their overall
            # finishing position (athlete.position) – not a category
            # sub-position.
            for athlete in race_result.athletes:
                key = (athlete.name, athlete.club)

                if key not in score_map:
                    score_map[key] = Score(
                        name=athlete.name,
                        club=athlete.club,
                        category=category_code,
                        round_scores={},
                    )

                score_map[key].add_round_score(round_number, athlete.position)

        updated_scores = list(score_map.values())

        # League rule: rank by best (n-1) rounds, where n is rounds processed.
        rounds_to_count = rounds_processed if rounds_processed <= 1 else rounds_processed - 1
        # Primary: total score (999999 for incomplete), secondary: more rounds
        # first, tertiary: lower aggregate score first.
        updated_scores.sort(
            key=lambda s: (
                s.calculate_total_score(rounds_to_count),
                -s.get_rounds_competed(),
                sum(sorted(s.round_scores.values())),
            )
        )

        # Apply head-to-head tiebreak for the top 4
        updated_scores = self._apply_head_to_head_tiebreak(updated_scores, rounds_to_count)

        self.score_repo.save_scores(category_code, updated_scores)
        logger.info(
            f"Saved {len(updated_scores)} overall scores for {category_code} "
            f"({rounds_processed} rounds processed)"
        )

    def update_all_categories(self) -> None:
        """Update scores for all individual categories.

        This includes:
        - INDIVIDUAL categories (adult categories like SM, MV40, etc.)
        - TEAM categories (youth categories like U9B, U9G, etc.) which also need individual scoring
        - OVERALL categories (e.g., MensOverall, WomensOverall)
        """
        individual_categories = self.config.category_config.get_categories_by_type(
            CategoryType.INDIVIDUAL
        )

        # Also include youth team categories which need individual scoring
        team_categories = self.config.category_config.get_categories_by_type(CategoryType.TEAM)
        # Filter to only include youth categories (exclude adult team categories like "Men", "Women")
        youth_team_categories = [
            cat for cat in team_categories if cat.age_group and cat.age_group.startswith("U")
        ]

        for category in individual_categories + youth_team_categories:
            self.update_scores_for_category(category.code)

        # Overall categories use the athlete's race-wide finishing position
        overall_categories = self.config.category_config.get_categories_by_type(
            CategoryType.OVERALL
        )
        for category in overall_categories:
            self.update_scores_for_overall_category(category.code)

    def _apply_head_to_head_tiebreak(
        self, scores: list[Score], rounds_to_count: int, top_n: int = 4
    ) -> list[Score]:
        """Re-sort tied athletes in the top N positions using head-to-head.

        For each group of athletes sharing the same total score within the
        top *top_n* positions, those athletes are re-ordered so that an
        athlete who beat another head-to-head in more rounds is ranked
        higher.

        Args:
            scores: Pre-sorted list of scores.
            rounds_to_count: Number of best rounds used for total score.
            top_n: Only consider ties within the first *top_n* positions.

        Returns:
            A new list with ties in the top N resolved by head-to-head.
        """
        if len(scores) <= 1:
            return scores

        # Only look at the top_n athletes (may expand if tie extends beyond)
        top = scores[:top_n]
        rest = scores[top_n:]

        # Group the top athletes by their total score
        groups: list[list[Score]] = []
        current_group: list[Score] = [top[0]]
        current_total = top[0].calculate_total_score(rounds_to_count)

        for s in top[1:]:
            total = s.calculate_total_score(rounds_to_count)
            if total == current_total:
                current_group.append(s)
            else:
                groups.append(current_group)
                current_group = [s]
                current_total = total
        groups.append(current_group)

        # Re-sort each tied group using head-to-head
        resolved: list[Score] = []
        for group in groups:
            if len(group) <= 1:
                resolved.extend(group)
            else:
                resolved.extend(self._sort_by_head_to_head(group))

        return resolved + rest

    @staticmethod
    def _head_to_head_wins(a: Score, b: Score) -> tuple[int, int]:
        """Count head-to-head wins between two athletes.

        A "win" is a round where both athletes competed and one had a
        lower (better) position than the other.

        Returns:
            (wins_for_a, wins_for_b)
        """
        common_rounds = set(a.round_scores) & set(b.round_scores)
        a_wins = 0
        b_wins = 0
        for r in common_rounds:
            if a.round_scores[r] < b.round_scores[r]:
                a_wins += 1
            elif b.round_scores[r] < a.round_scores[r]:
                b_wins += 1
        return a_wins, b_wins

    def _sort_by_head_to_head(self, group: list[Score]) -> list[Score]:
        """Sort a tied group of scores using pairwise head-to-head results.

        Uses a comparison function: athlete A is ranked higher than B if A
        has more head-to-head wins against B across the rounds they both
        raced.  If head-to-head is also tied, the original order is
        preserved.
        """

        def cmp(a: Score, b: Score) -> int:
            a_wins, b_wins = self._head_to_head_wins(a, b)
            if a_wins > b_wins:
                return -1  # a ranks higher
            if b_wins > a_wins:
                return 1  # b ranks higher
            return 0  # keep original order

        return sorted(group, key=functools.cmp_to_key(cmp))

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
