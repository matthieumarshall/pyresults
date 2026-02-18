"""PDF output generator implementation."""

import logging
from pathlib import Path

import pandas as pd
from fpdf import FPDF

from pyresults.config import CompetitionConfig

from .interfaces import IOutputGenerator
from .score_data_provider import CategoryDisplayData, ScoreDataProvider

logger = logging.getLogger(__name__)


class CustomPDF(FPDF):
    """Custom PDF class with header and footer."""

    def __init__(self, league_title: str):
        super().__init__()
        self.league_title = league_title

    def header(self):
        """Page header."""
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self.league_title, 0, 1, "C")
        self.ln(5)

    def footer(self):
        """Page footer."""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


class PdfOutputGenerator(IOutputGenerator):
    """Generates PDF output from pre-computed score data.

    This class is a pure rendering layer.  All score computation and data
    preparation is handled by ``ScoreDataProvider``; this generator only
    converts the resulting DataFrames into styled PDF tables.
    """

    def __init__(self, config: CompetitionConfig, output_path: Path):
        """Initialize PDF generator.

        Args:
            config: Competition configuration
            output_path: Path where PDF file should be saved
        """
        self.config = config
        self.output_path = output_path
        self.data_provider = ScoreDataProvider(config)

    def generate(self) -> None:
        """Generate PDF file with all score tables."""
        logger.info(f"Generating PDF output to {self.output_path}")

        pdf = CustomPDF("Oxfordshire Cross Country League 2025-2026")
        pdf.set_auto_page_break(auto=True, margin=15)

        # Get display-ready data for every category
        all_data = self.data_provider.get_all_category_data()
        logger.debug(f"Found {len(all_data)} categories to include in PDF")

        for category_data in all_data:
            self._add_category_table(pdf, category_data)

        # Save PDF
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            pdf.output(str(self.output_path))
            logger.info(f"Successfully saved PDF file to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF file to {self.output_path}: {e}")
            raise OSError(f"Failed to save PDF file to {self.output_path}: {e}") from e

    def _add_category_table(self, pdf: FPDF, data: CategoryDisplayData) -> None:
        """Add a table for a specific category.

        Args:
            pdf: PDF object to add table to
            data: Pre-computed display data for a single category
        """
        df = data.dataframe

        # Limit to top results to fit on page
        df = df.head(50)

        # Start new page for this category
        pdf.add_page()

        # Category title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, data.title, 0, 1, "C")
        pdf.ln(5)

        # Calculate column widths
        page_width = pdf.w - 2 * pdf.l_margin

        col_widths = []
        for col in df.columns:
            if col == "Name":
                col_widths.append(50)
            elif col == "Club":
                col_widths.append(80 if data.is_team else 45)
            elif col == "Team":
                col_widths.append(80)
            elif col in ("R 1", "R 2", "R 3", "R 4", "R 5", "Score"):
                col_widths.append(15)
            elif col == "Pos":
                col_widths.append(15)
            elif col.startswith("Runner"):
                col_widths.append(50)
            else:
                col_widths.append(20)

        # Scale if total exceeds page width
        total_width = sum(col_widths)
        if total_width > page_width:
            scale = page_width / total_width
            col_widths = [w * scale for w in col_widths]

        # Table header
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(200, 200, 200)
        for col, width in zip(df.columns, col_widths, strict=False):
            pdf.cell(width, 8, str(col), 1, 0, "C", True)
        pdf.ln()

        # Table rows
        pdf.set_font("Arial", "", 9)
        for _, row in df.iterrows():
            for col_name, value, width in zip(df.columns, row, col_widths, strict=False):
                display_value = self._format_cell(value)

                # Truncate long text
                max_chars = 40 if col_name in ("Name", "Club", "Team") else 12
                if len(display_value) > max_chars:
                    display_value = display_value[: max_chars - 3] + "..."

                alignment = "L" if col_name in ("Name", "Club", "Team") else "C"
                pdf.cell(width, 7, display_value, 1, 0, alignment)
            pdf.ln()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_cell(value) -> str:
        """Format a single cell value for PDF display."""
        if pd.isna(value):
            return ""
        try:
            num = float(value)
            return str(int(num)) if num == int(num) else str(value)
        except (ValueError, TypeError):
            return str(value)
