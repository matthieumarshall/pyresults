"""Team score aggregation service."""

import logging

from pyresults.config import CompetitionConfig
from pyresults.domain import Score
from pyresults.repositories import IRaceResultRepository, IScoreRepository, ITeamResultRepository

from .team_scoring_service import TeamScoringService

logger = logging.getLogger(__name__)


class TeamScoreService:
    """Service for aggregating team scores across rounds.

    This service handles:
    - Loading team results for each round via ITeamResultRepository
    - Building cumulative team scores
    - Calculating total scores based on all rounds
    - Persisting updated team scores via IScoreRepository

    Dependencies are injected so that CSV, in-memory, or database
    implementations can be substituted without touching this class.
    """

    def __init__(
        self,
        config: CompetitionConfig,
        race_result_repo: IRaceResultRepository,
        team_result_repo: ITeamResultRepository,
        team_score_repo: IScoreRepository,
        team_scoring_service: TeamScoringService,
    ):
        """Initialize service with dependencies.

        Args:
            config: Competition configuration
            race_result_repo: Repository for loading race results (retained for
                future use, e.g. recalculating team results on the fly)
            team_result_repo: Repository for per-round team result rows
            team_score_repo: Repository for persisting aggregated team scores
            team_scoring_service: Service for calculating team scores
        """
        self.config = config
        self.race_result_repo = race_result_repo
        self.team_result_repo = team_result_repo
        self.team_score_repo = team_score_repo
        self.team_scoring_service = team_scoring_service

    def update_team_scores_for_category(self, category_code: str) -> None:
        """Update team scores for a specific category across all rounds.

        Args:
            category_code: Team category code (e.g., "U13B", "Men")
        """
        logger.info(f"Updating team scores for category: {category_code}")

        category = self.config.category_config.get_category(category_code)

        if not category.is_team_category():
            logger.warning(f"Category {category_code} is not a team category, skipping")
            return

        score_map: dict[str, Score] = {}
        rounds_processed = 0

        for round_number in self.config.round_numbers:
            if not self.team_result_repo.team_results_exist(category_code, round_number):
                logger.debug(f"No team results for {category_code} in {round_number}")
                continue

            rounds_processed += 1

            rows = self.team_result_repo.load_team_results(category_code, round_number)

            for idx, row in enumerate(rows):
                # Support both "team" (new format with labels) and "club" (old format)
                team_name = row.get("team", row.get("club", "Unknown"))

                round_score: int
                if "score" in row and row["score"] not in (None, ""):
                    try:
                        round_score = int(float(row["score"]))
                    except (TypeError, ValueError):
                        logger.debug(
                            f"Invalid score '{row.get('score')}' for {team_name} in "
                            f"{round_number}, falling back to position"
                        )
                        round_score = int(row["pos"]) if "pos" in row else idx + 1
                else:
                    round_score = int(row["pos"]) if "pos" in row else idx + 1

                if team_name not in score_map:
                    score_map[team_name] = Score(
                        name=team_name,
                        club=None,
                        category=category_code,
                        round_scores={},
                    )

                score_map[team_name].add_round_score(round_number, round_score)

        team_scores = list(score_map.values())

        # Team scores use all rounds (no dropped round).
        team_scores.sort(
            key=lambda s: (
                s.calculate_total_score(rounds_processed),
                -s.get_rounds_competed(),
                sum(sorted(s.round_scores.values())),
            )
        )

        self.team_score_repo.save_scores(category_code, team_scores)
        logger.info(
            f"Saved {len(team_scores)} team scores for {category_code} "
            f"({rounds_processed} rounds processed)"
        )

    def update_all_team_categories(self) -> None:
        """Update scores for all team categories."""
        team_category_codes = [
            "U9B",
            "U9G",
            "U11B",
            "U11G",
            "U13B",
            "U13G",
            "U15B",
            "U15G",
            "U17M",
            "U17W",
            "Men",
            "Women",
        ]

        for category_code in team_category_codes:
            try:
                self.update_team_scores_for_category(category_code)
            except ValueError as e:
                logger.warning(f"Could not update team scores for {category_code}: {e}")
                continue
