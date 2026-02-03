"""PDF output generator implementation."""

import logging
from pathlib import Path

import pandas as pd
from fpdf import FPDF

from pyresults.config import CompetitionConfig

from .interfaces import IOutputGenerator

logger = logging.getLogger(__name__)


class CustomPDF(FPDF):
    """Custom PDF class with header and footer."""

    def __init__(self, title: str):
        super().__init__()
        self.title_text = title

    def header(self):
        """Page header."""
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, self.title_text, 0, 1, "C")
        self.ln(5)

    def footer(self):
        """Page footer."""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


class PdfOutputGenerator(IOutputGenerator):
    """Generates PDF output from score data.

    This class handles:
    - Loading score data from CSV files
    - Formatting data for PDF tables
    - Creating styled PDF documents
    - Saving PDF files

    This replaces the create_pdf function, following the
    Single Responsibility Principle and Interface Segregation Principle.
    """

    def __init__(self, config: CompetitionConfig, output_path: Path):
        """Initialize PDF generator.

        Args:
            config: Competition configuration
            output_path: Path where PDF file should be saved
        """
        self.config = config
        self.output_path = output_path

    def generate(self) -> None:
        """Generate PDF file with all score tables."""
        logger.info(f"Generating PDF output to {self.output_path}")

        pdf = CustomPDF("Oxfordshire XC League Results")
        pdf.set_auto_page_break(auto=True, margin=15)

        # Get all categories to include
        categories = self._get_categories_to_include()
        logger.debug(f"Found {len(categories)} categories to include in PDF")

        # Add a table for each category
        for category_code in categories:
            self._add_category_table(pdf, category_code)

        # Save PDF
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            pdf.output(str(self.output_path))
            logger.info(f"Successfully saved PDF file to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF file to {self.output_path}: {e}")
            raise OSError(f"Failed to save PDF file to {self.output_path}: {e}")

    def _get_categories_to_include(self) -> list[str]:
        """Get ordered list of category codes to include in PDF.

        Returns:
            List of category codes in desired order
        """
        # Define the order: individual followed by team for each age group
        # Order: U9G, Team U9G, U9B, Team U9B, U11G, Team U11G, etc.
        youth_order = [
            ("U9G", "U9G"),
            ("U9B", "U9B"),
            ("U11G", "U11G"),
            ("U11B", "U11B"),
            ("U13G", "U13G"),
            ("U13B", "U13B"),
            ("U15G", "U15G"),
            ("U15B", "U15B"),
            ("U17W", "U17W"),
            ("U17M", "U17M"),
        ]

        senior_order = [
            "U20W",
            "U20M",
            "SW",
            "SM",
            "WV40",
            "MV40",
            "WV50",
            "MV50",
            "WV60",
            "MV60",
            "WV70",
            "MV70",
        ]

        overall_order = [("MensOverall", None), ("WomensOverall", None)]

        adult_teams = [("Women", "Women"), ("Men", "Men")]

        # Filter to only include categories that have score files
        categories = []
        scores_dir = self.config.data_base_path / "scores"
        teams_dir = scores_dir / "teams"

        # Add youth categories (individual + team pairs)
        for individual_code, team_code in youth_order:
            # Add individual
            csv_path = scores_dir / f"{individual_code}.csv"
            if csv_path.exists():
                categories.append(individual_code)

            # Add team if exists
            if teams_dir.exists():
                team_csv_path = teams_dir / f"{team_code}.csv"
                if team_csv_path.exists():
                    categories.append(f"Team {team_code}")

        # Add senior/vet categories (no teams for these)
        for category_code in senior_order:
            csv_path = scores_dir / f"{category_code}.csv"
            if csv_path.exists():
                categories.append(category_code)

        # Add adult teams
        if teams_dir.exists():
            for individual_code, team_code in adult_teams:
                team_csv_path = teams_dir / f"{team_code}.csv"
                if team_csv_path.exists():
                    categories.append(f"Team {team_code}")

        # Add overall categories at the end
        for category_code, _ in overall_order:
            csv_path = scores_dir / f"{category_code}.csv"
            if csv_path.exists():
                categories.append(category_code)

        return categories

    def _format_team_title(self, category_code: str) -> str:
        """Format team category code into readable title.

        Args:
            category_code: Category code (e.g., "U9B", "Men")

        Returns:
            Formatted title (e.g., "U9 Boys Teams", "Men's Teams")
        """
        team_titles = {
            "U9B": "U9 Boys Teams",
            "U9G": "U9 Girls Teams",
            "U11B": "U11 Boys Teams",
            "U11G": "U11 Girls Teams",
            "U13B": "U13 Boys Teams",
            "U13G": "U13 Girls Teams",
            "U15B": "U15 Boys Teams",
            "U15G": "U15 Girls Teams",
            "U17M": "U17 Men's Teams",
            "U17W": "U17 Women's Teams",
            "Men": "Men's Teams",
            "Women": "Women's Teams",
        }

        return team_titles.get(category_code, f"Team {category_code}")

    def _add_category_table(self, pdf: FPDF, category_code: str) -> None:
        """Add a table for a specific category.

        Args:
            pdf: PDF object to add table to
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

        # Start new page for this category
        pdf.add_page()

        # Add category title
        if is_team:
            # For team categories, convert code to readable name
            title = self._format_team_title(actual_category)
        else:
            try:
                category = self.config.category_config.get_category(category_code)
                title = category.name
            except (ValueError, KeyError) as e:
                logger.warning(
                    f"Could not find category name for {category_code}, using code as title: {e}"
                )
                title = category_code

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, title, 0, 1, "C")
        pdf.ln(5)

        # Prepare table data
        # Filter out empty rows - check for Name column (individual) or Club column (team)
        if "Name" in df.columns:
            df = df[df["Name"].notna()]
        elif "Club" in df.columns:
            df = df[df["Club"].notna()]

        # Rename round columns for better readability
        column_renames = {"r1": "R 1", "r2": "R 2", "r3": "R 3", "r4": "R 4", "r5": "R 5"}
        df = df.rename(columns=column_renames)

        # Limit to top results to fit on page
        df = df.head(50)

        # Calculate column widths - make Name and Club wider
        page_width = pdf.w - 2 * pdf.l_margin

        # Define custom widths for different column types
        col_widths = []
        for col in df.columns:
            if col == "Name":
                col_widths.append(50)  # Wider for names
            elif col == "Club":
                # Much wider for clubs in team results, normal in individual results
                col_widths.append(80 if is_team else 45)
            elif col == "team":
                col_widths.append(80)  # Much wider for team names
            elif col in ["R 1", "R 2", "R 3", "R 4", "R 5", "score"]:
                col_widths.append(15)  # Narrow for numbers
            elif col == "Pos" or col == "Score":
                col_widths.append(15)  # Narrow for position/score
            elif col.startswith("Runner"):
                col_widths.append(50)  # Wider for runner names in team results
            else:
                col_widths.append(20)  # Default width

        # Adjust if total width exceeds page width
        total_width = sum(col_widths)
        if total_width > page_width:
            scale_factor = page_width / total_width
            col_widths = [w * scale_factor for w in col_widths]

        # Add table header
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(200, 200, 200)

        for col, width in zip(df.columns, col_widths, strict=False):
            pdf.cell(width, 8, str(col), 1, 0, "C", True)
        pdf.ln()

        # Add table rows
        pdf.set_font("Arial", "", 9)

        for _, row in df.iterrows():
            for col_name, value, width in zip(df.columns, row, col_widths, strict=False):
                # Convert value to string, handle NaN
                if pd.isna(value):
                    display_value = ""
                else:
                    # Format numeric values as integers (no decimals)
                    try:
                        # Try to convert to float first, then to int
                        num_value = float(value)
                        if num_value == int(num_value):  # If it's a whole number
                            display_value = str(int(num_value))
                        else:
                            display_value = str(value)
                    except (ValueError, TypeError):
                        display_value = str(value)

                # Truncate text if too long, but allow more space for Name/Club/team
                max_chars = 40 if col_name in ["Name", "Club", "team"] else 12
                if len(display_value) > max_chars:
                    display_value = display_value[: max_chars - 3] + "..."

                # Left align for text, center for numbers
                alignment = "L" if col_name in ["Name", "Club", "team"] else "C"
                pdf.cell(width, 7, display_value, 1, 0, alignment)
            pdf.ln()
