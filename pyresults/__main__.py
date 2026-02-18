"""Generates standings for Oxon XC League a season.

This module serves as the entry point for the application, using the new
SOLID-based architecture with dependency injection.
"""

import logging
import sys
from argparse import ArgumentParser

from pyresults.config import build_default_config
from pyresults.logging_config import setup_logging
from pyresults.results_processor import ResultsProcessor

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = ArgumentParser(description="Generates standings for Oxon XC League 2024/25 season.")
    parser.add_argument(
        "--rounds",
        nargs="+",
        default=["r1", "r2", "r3", "r4", "r5"],
        help="List of rounds to process (e.g. --rounds r1 r2 r3)",
    )
    parser.add_argument("--excel", action="store_true", default=False, help="Generate Excel output")
    parser.add_argument("--pdf", action="store_true", default=False, help="Generate PDF output")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO)",
    )
    args = parser.parse_args()

    # Initialize logging
    setup_logging(level=args.log_level)

    try:
        # Build configuration (could be loaded from file in future)
        config = build_default_config()

        # Create processor with dependency injection
        processor = ResultsProcessor(config)

        # Process rounds and generate outputs
        processor.process_rounds(
            rounds_to_process=args.rounds, create_excel=args.excel, create_pdf=args.pdf
        )

        logger.info("Processing completed successfully")

    except Exception as e:
        logger.critical(f"Application failed with error: {e}", exc_info=True)
        sys.exit(1)
