"""Excel output generator implementation."""

import logging
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

from pyresults.config import CompetitionConfig

from .interfaces import IOutputGenerator

logger = logging.getLogger(__name__)


class ExcelOutputGenerator(IOutputGenerator):
    """Generates Excel output from score data.

    This class handles:
    - Loading score data from CSV files
    - Formatting data for Excel
    - Creating styled Excel workbooks
    - Saving Excel files

    This replaces the create_excel function, following the
    Single Responsibility Principle and Interface Segregation Principle.
    """

    def __init__(self, config: CompetitionConfig, output_path: Path):
        """Initialize Excel generator.

        Args:
            config: Competition configuration
            output_path: Path where Excel file should be saved
        """
        self.config = config
        self.output_path = output_path

    def generate(self) -> None:
        """Generate Excel file with all score sheets."""
        logger.info(f"Generating Excel output to {self.output_path}")

        wb = Workbook()
        if wb.active:
            wb.remove(wb.active)  # Remove default sheet

        # Get all categories to include
        categories = self._get_categories_to_include()
        logger.debug(f"Found {len(categories)} categories to include in Excel")

        # Create a sheet for each category
        for category_code in categories:
            self._add_category_sheet(wb, category_code)

        # Save workbook
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            wb.save(self.output_path)
            logger.info(f"Successfully saved Excel file to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save Excel file to {self.output_path}: {e}")
            raise OSError(f"Failed to save Excel file to {self.output_path}: {e}") from e

    def _get_categories_to_include(self) -> list[str]:
        """Get list of category codes to include in Excel output.

        Returns:
            List of category codes
        """
        # Include all categories that have score files
        categories = []
        scores_dir = self.config.data_base_path / "scores"

        if not scores_dir.exists():
            return []

        for csv_file in scores_dir.glob("*.csv"):
            categories.append(csv_file.stem)

        # Also include team scores
        teams_dir = scores_dir / "teams"
        if teams_dir.exists():
            for csv_file in teams_dir.glob("*.csv"):
                categories.append(f"Team {csv_file.stem}")

        return categories

    def _add_category_sheet(self, wb: Workbook, category_code: str) -> None:
        """Add a sheet for a specific category.

        Args:
            wb: Workbook to add sheet to
            category_code: Category code
        """
        # Determine if this is a team category
        is_team = category_code.startswith("Team ")

        if is_team:
            actual_category = category_code.replace("Team ", "")
            csv_path = self.config.data_base_path / "scores" / "teams" / f"{actual_category}.csv"
        else:
            csv_path = self.config.data_base_path / "scores" / f"{category_code}.csv"

        if not csv_path.exists():
            return

        # Load data
        df = pd.read_csv(csv_path)

        # Create sheet with truncated name (Excel has 31 char limit)
        sheet_name = category_code[:31]
        ws = wb.create_sheet(title=sheet_name)

        # Write data to sheet
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)

                # Style header row
                if r_idx == 1:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(
                        start_color="DDDDDD", end_color="DDDDDD", fill_type="solid"
                    )
                    cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except (TypeError, AttributeError) as e:
                    # Skip cells with problematic values
                    logger.debug(f"Skipping cell value in column {column_letter}: {e}")
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
