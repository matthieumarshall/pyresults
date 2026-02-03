"""Main application orchestrator.

This module provides the top-level coordinator that wires together all
services and orchestrates the results processing workflow.
"""

import logging
from pathlib import Path

from pyresults.config import CompetitionConfig
from pyresults.output import (
    ExcelOutputGenerator,
    IOutputGenerator,
    PdfOutputGenerator,
)
from pyresults.repositories import (
    CsvRaceResultRepository,
    CsvScoreRepository,
)
from pyresults.services import (
    IndividualScoreService,
    RaceProcessorService,
    TeamScoreService,
    TeamScoringService,
)

logger = logging.getLogger(__name__)


class ResultsProcessor:
    """Main application orchestrator with dependency injection.

    This class replaces the old Results class, following SOLID principles:
    - Single Responsibility: Only orchestrates the workflow
    - Dependency Inversion: Depends on abstractions (interfaces)
    - Open/Closed: Can be extended with new output generators without modification

    All dependencies are injected, making the system testable and flexible.
    """

    def __init__(self, config: CompetitionConfig):
        """Initialize processor with configuration.

        Args:
            config: Competition configuration
        """
        self.config = config

        # Initialize repositories
        self.race_result_repo = CsvRaceResultRepository(base_path=config.data_base_path)
        self.score_repo = CsvScoreRepository(
            base_path=config.data_base_path / "scores", round_numbers=config.round_numbers
        )

        # Initialize services
        self.race_processor = RaceProcessorService(config=config, repository=self.race_result_repo)
        self.individual_score_service = IndividualScoreService(
            config=config, race_result_repo=self.race_result_repo, score_repo=self.score_repo
        )
        self.team_scoring_service = TeamScoringService(config=config)
        self.team_score_service = TeamScoreService(
            config=config,
            race_result_repo=self.race_result_repo,
            team_scoring_service=self.team_scoring_service,
        )

        # Output generators (can be swapped or extended)
        self.output_generators: list[IOutputGenerator] = []

    def process_rounds(
        self, rounds_to_process: list[str], create_excel: bool = False, create_pdf: bool = False
    ) -> None:
        """Process race results and generate outputs.

        This is the main entry point that orchestrates the entire workflow:
        1. Process raw race result files
        2. Calculate team scores
        3. Aggregate individual scores
        4. Aggregate team scores
        5. Generate output files

        Args:
            rounds_to_process: List of round identifiers to process (e.g., ["r1", "r2"])
            create_excel: Whether to generate Excel output
            create_pdf: Whether to generate PDF output
        """
        # Step 1: Process race result files for each round
        for round_number in rounds_to_process:
            self._process_round(round_number)

        # Step 2: Aggregate individual scores across all rounds
        self._update_individual_scores()

        # Step 3: Aggregate team scores across all rounds
        self._update_team_scores()

        # Step 4: Generate output files
        if create_excel or create_pdf:
            self._generate_outputs(create_excel, create_pdf)

    def _process_round(self, round_number: str) -> None:
        """Process all race result files for a given round.

        Args:
            round_number: Round identifier (e.g., "r1", "r2")
        """
        # Find all race result files in the input directory for this round
        input_dir = Path("./input_data") / round_number

        if not input_dir.exists():
            logger.warning(f"Input directory not found: {input_dir}")
            return

        # Process each CSV file in the round directory
        for race_file in input_dir.glob("*.csv"):
            logger.info(f"Processing {race_file.name}...")

            # Process and save race result
            race_result = self.race_processor.process_and_save(race_file)

            # Calculate and save team scores for this race
            self._process_team_scores_for_race(race_result)

    def _process_team_scores_for_race(self, race_result) -> None:
        """Calculate and save team scores for a race.

        Args:
            race_result: Processed race result
        """
        # Get team categories for this race
        team_categories = self.team_scoring_service.get_team_categories_for_race(
            race_result.race_name
        )

        # Calculate teams for each category
        for category_code in team_categories:
            try:
                category = self.config.category_config.get_category(category_code)
                teams = self.team_scoring_service.calculate_teams_for_race(race_result, category)

                # Validate team_size
                if category.team_size is None:
                    logger.warning(f"Category {category_code} has no team_size defined")
                    continue

                # Save team results to CSV
                self._save_team_results(
                    teams, category_code, race_result.round_number, category.team_size
                )
            except ValueError as e:
                # Category might not exist or not be a team category
                logger.warning(f"Could not process teams for {category_code}: {e}")
                continue

    def _save_team_results(
        self, teams, category_code: str, round_number: str, team_size: int
    ) -> None:
        """Save team results to CSV file.

        Args:
            teams: List of Team objects
            category_code: Category code
            round_number: Round identifier
            team_size: Number of athletes per team
        """
        import pandas as pd

        # Create team result data
        result_data = self.team_scoring_service.create_team_result_data(teams, team_size)

        if not result_data:
            return

        # Save to CSV
        output_path = self.config.data_base_path / round_number / "teams" / f"{category_code}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(result_data)
        df.to_csv(output_path, index=False)

    def _update_individual_scores(self) -> None:
        """Update individual scores for all categories."""
        logger.info("Updating individual scores...")
        self.individual_score_service.update_all_categories()

    def _update_team_scores(self) -> None:
        """Update team scores for all categories."""
        logger.info("Updating team scores...")
        self.team_score_service.update_all_team_categories()

    def _generate_outputs(self, create_excel: bool, create_pdf: bool) -> None:
        """Generate output files.

        Args:
            create_excel: Whether to generate Excel output
            create_pdf: Whether to generate PDF output
        """
        if create_excel:
            logger.info("Generating Excel output...")
            excel_generator = ExcelOutputGenerator(
                config=self.config, output_path=Path("./output/results.xlsx")
            )
            excel_generator.generate()

        if create_pdf:
            logger.info("Generating PDF output...")
            pdf_generator = PdfOutputGenerator(
                config=self.config, output_path=Path("./output/results.pdf")
            )
            pdf_generator.generate()
