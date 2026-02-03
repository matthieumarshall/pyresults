"""Team score aggregation service."""

import logging
from pathlib import Path

import pandas as pd

from pyresults.config import CompetitionConfig
from pyresults.domain import Score
from pyresults.repositories import IRaceResultRepository

from .team_scoring_service import TeamScoringService

logger = logging.getLogger(__name__)


class TeamScoreService:
    """Service for aggregating team scores across rounds.

    This service handles:
    - Loading team results for each round
    - Building cumulative team scores
    - Calculating total scores based on best N rounds
    - Persisting updated team scores

    This replaces the Results.update_team_scores() logic,
    following the Single Responsibility Principle.
    """

    def __init__(
        self,
        config: CompetitionConfig,
        race_result_repo: IRaceResultRepository,
        team_scoring_service: TeamScoringService,
    ):
        """Initialize service with dependencies.

        Args:
            config: Competition configuration
            race_result_repo: Repository for loading race results
            team_scoring_service: Service for calculating team scores
        """
        self.config = config
        self.race_result_repo = race_result_repo
        self.team_scoring_service = team_scoring_service

    def update_team_scores_for_category(self, category_code: str) -> None:
        """Update team scores for a specific category across all rounds.

        Args:
            category_code: Team category code (e.g., "U13B", "Men")
        """
        logger.info(f"Updating team scores for category: {category_code}")

        # Get category configuration
        category = self.config.category_config.get_category(category_code)

        if not category.is_team_category():
            logger.warning(f"Category {category_code} is not a team category, skipping")
            return

        # Build team score map
        score_map: dict[str, Score] = {}

        # Process each round
        rounds_processed = 0
        for round_number in self.config.round_numbers:
            # Check if team results exist for this round
            team_results_path = self._get_team_results_path(category_code, round_number)

            if not team_results_path.exists():
                logger.debug(f"No team results for {category_code} in {round_number}")
                continue

            rounds_processed += 1

            # Load team results for this round
            try:
                df = pd.read_csv(team_results_path)
            except Exception as e:
                logger.error(f"Failed to read team results from {team_results_path}: {e}")
                continue

            # Update scores for each club
            for _, row in df.iterrows():
                club = row["Club"]
                position = int(row["Pos"])

                if club not in score_map:
                    # Create new score entry
                    score = Score(
                        name=club,
                        club=None,  # For teams, club is the name
                        category=category_code,
                        round_scores={},
                    )
                    score_map[club] = score

                # Add this round's position
                score_map[club].add_round_score(round_number, position)

        # Convert to list and save
        team_scores = list(score_map.values())

        # Calculate rounds to count (all rounds minus 1, minimum 1)
        rounds_to_count = max(1, rounds_processed - 1) if rounds_processed > 0 else 0

        # Sort by total score
        team_scores.sort(key=lambda s: s.calculate_total_score(rounds_to_count))

        # Save updated scores
        self._save_team_scores(category_code, team_scores)
        logger.info(
            f"Saved {len(team_scores)} team scores for {category_code} "
            f"({rounds_processed} rounds processed)"
        )

    def update_all_team_categories(self) -> None:
        """Update scores for all team categories."""
        # Note: We need to process team categories that match the original naming
        # The original code used race names with specific mappings
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
                # Category might not exist or not be a team category
                logger.warning(f"Could not update team scores for {category_code}: {e}")
                continue

    def _get_team_results_path(self, category_code: str, round_number: str) -> Path:
        """Get path to team results CSV file.

        Args:
            category_code: Category code
            round_number: Round identifier

        Returns:
            Path to team results file
        """
        return self.config.data_base_path / round_number / "teams" / f"{category_code}.csv"

    def _save_team_scores(self, category_code: str, scores: list[Score]) -> None:
        """Save team scores to CSV file.

        Args:
            category_code: Category code
            scores: List of Score objects
        """
        output_path = self.config.data_base_path / "scores" / "teams" / f"{category_code}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        data = []
        for score in scores:
            row = {
                "Club": score.name,
            }

            # Add round scores
            for round_num in self.config.round_numbers:
                if round_num in score.round_scores:
                    row[round_num] = str(score.round_scores[round_num])
                else:
                    row[round_num] = ""

            # Calculate total
            rounds_to_count = max(1, len(score.round_scores) - 1) if score.round_scores else 0
            total = score.calculate_total_score(rounds_to_count)
            row["score"] = "" if total > 99999 else str(total)

            data.append(row)

        df = pd.DataFrame(data)

        # Ensure columns are in correct order
        columns = ["Club"] + self.config.round_numbers + ["score"]
        for col in columns:
            if col not in df.columns:
                df[col] = ""

        df = df[columns]
        try:
            df.to_csv(output_path, index=False)
            logger.debug(f"Saved team scores to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save team scores to {output_path}: {e}")
            raise OSError(f"Failed to save team scores to {output_path}: {e}") from e
