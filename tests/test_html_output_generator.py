"""Tests for HtmlOutputGenerator.

Ensures that:
- HTML output is generated without errors for all category types
- All category tables are present in the output
- Tooltip data is correctly embedded for team score cells
- Row-limiting logic matches the PDF generator
- The HTML is a well-formed self-contained document
"""

import re

import pytest

from pyresults.config import build_default_config
from pyresults.output.html_output_generator import HtmlOutputGenerator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_config(tmp_path):
    """Return a CompetitionConfig that uses tmp_path for data."""
    config = build_default_config()
    config.data_base_path = tmp_path / "data"
    return config


def _write_csv(path, text):
    """Write a CSV string to *path*, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Basic HTML structure
# ---------------------------------------------------------------------------


class TestHtmlStructure:
    """Verify that the generated HTML is a well-formed self-contained document."""

    def test_generates_valid_html_file(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE html>")
        assert "<html" in content
        assert "</html>" in content

    def test_html_contains_league_title(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Oxfordshire Cross Country League" in content

    def test_output_directory_created_automatically(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        deep_path = tmp_path / "a" / "b" / "c" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=deep_path)
        generator.generate()

        assert deep_path.exists()

    def test_empty_scores_produces_html(self, tmp_config, tmp_path):
        """Even with no score data the generator should produce a valid HTML file."""
        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_embedded_css_and_js(self, tmp_config, tmp_path):
        """The output must be self-contained (embedded CSS + JS, no external deps)."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "<style>" in content
        assert "<script>" in content
        # No external links
        assert 'href="http' not in content
        assert 'src="http' not in content


# ---------------------------------------------------------------------------
# Category tables
# ---------------------------------------------------------------------------


class TestCategoryTables:
    """Verify that category tables appear correctly in the HTML."""

    def test_category_title_present(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Under 13 Boys" in content

    def test_athlete_name_in_table(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice Smith,Oxford,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Alice Smith" in content

    def test_multiple_categories_present(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")
        _write_csv(scores / "SM.csv", "Name,Club,r1,score\nBob,D,2,2")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Under 13 Boys" in content
        assert "Senior Men" in content

    def test_navigation_links_present(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # Navigation sidebar should contain a link to the category
        assert '<a href="#' in content

    def test_team_table_present(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "U13 Boys Teams" in content
        assert "Oxford AC A" in content


# ---------------------------------------------------------------------------
# Row limiting
# ---------------------------------------------------------------------------


class TestRowLimiting:
    """Verify that the max_rows parameter is honoured."""

    def _csv_with_n_rows(self, n: int) -> str:
        header = "Name,Club,r1,score"
        rows = [f"Athlete{i},Club,{i},{i}" for i in range(1, n + 1)]
        return "\n".join([header] + rows)

    def test_max_rows_limits_output(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", self._csv_with_n_rows(20))

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path, max_rows=5)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # Athlete6 should not appear when max_rows=5
        assert "Athlete5" in content
        assert "Athlete6" not in content

    def test_default_50_row_limit(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", self._csv_with_n_rows(60))

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Athlete50" in content
        assert "Athlete51" not in content


# ---------------------------------------------------------------------------
# Tooltip / interactive features
# ---------------------------------------------------------------------------


class TestTooltips:
    """Verify that interactive tooltip data is embedded for team score cells."""

    def test_no_tooltip_without_per_round_data(self, tmp_config, tmp_path):
        """When no per-round team files exist, no tooltip attributes are added."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # data-tooltip=" (with value) must not appear — the bare string exists in JS
        assert 'data-tooltip="' not in content

    def test_tooltip_added_when_per_round_data_present(self, tmp_config, tmp_path):
        """When per-round data with runners exists, data-tooltip attrs are added."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        # Write per-round team result file with runner info
        per_round = tmp_config.data_base_path / "r1" / "teams" / "U13B.csv"
        _write_csv(
            per_round,
            "Pos,Team,Score,Runner1,Runner2,Runner3\n"
            "1,Oxford AC A,6,Alice Smith (1),Bob Jones (2),Charlie Brown (3)",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert 'data-tooltip="' in content

    def test_tooltip_contains_athlete_names(self, tmp_config, tmp_path):
        """Tooltip content should include athlete name from the runner data."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        per_round = tmp_config.data_base_path / "r1" / "teams" / "U13B.csv"
        _write_csv(
            per_round,
            "Pos,Team,Score,Runner1,Runner2,Runner3\n"
            "1,Oxford AC A,6,Alice Smith (1),Bob Jones (2),Charlie Brown (3)",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # The athlete names should appear in a data-tooltip attribute value
        assert "Alice Smith" in content
        assert "Bob Jones" in content
        assert "Charlie Brown" in content

    def test_tooltip_has_tooltip_css_class(self, tmp_config, tmp_path):
        """Cells with tooltips should carry the has-tooltip CSS class."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        per_round = tmp_config.data_base_path / "r1" / "teams" / "U13B.csv"
        _write_csv(
            per_round,
            "Pos,Team,Score,Runner1,Runner2\n1,Oxford AC A,6,Alice (1),Bob (2)",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "has-tooltip" in content

    def test_individual_category_has_no_tooltip(self, tmp_config, tmp_path):
        """Individual (non-team) category tables should never have tooltips."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,score\nAlice Smith,Oxford,1,1\nBob Jones,Banbury,2,2",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # data-tooltip=" (with value) must not appear for individual categories
        assert 'data-tooltip="' not in content

    def test_tooltip_javascript_present(self, tmp_config, tmp_path):
        """The page must include the JavaScript that drives tooltip display."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nOxford AC A,6,6")

        per_round = tmp_config.data_base_path / "r1" / "teams" / "U13B.csv"
        _write_csv(
            per_round,
            "Pos,Team,Score,Runner1,Runner2\n1,Oxford AC A,6,Alice (1),Bob (2)",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "getElementById('tooltip')" in content or 'getElementById("tooltip")' in content

    def test_total_score_tooltip_aggregates_rounds(self, tmp_config, tmp_path):
        """The Score cell tooltip should mention multiple rounds."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,r2,score\nOxford AC A,6,8,14")

        per_round_r1 = tmp_config.data_base_path / "r1" / "teams" / "U13B.csv"
        _write_csv(
            per_round_r1,
            "Pos,Team,Score,Runner1,Runner2\n1,Oxford AC A,6,Alice (1),Bob (2)",
        )
        per_round_r2 = tmp_config.data_base_path / "r2" / "teams" / "U13B.csv"
        _write_csv(
            per_round_r2,
            "Pos,Team,Score,Runner1,Runner2\n1,Oxford AC A,8,Alice (3),Charlie (5)",
        )

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # Both rounds should appear in the total score tooltip
        assert "R 1" in content
        assert "R 2" in content


# ---------------------------------------------------------------------------
# Category ordering (mirrors PdfOutputGenerator)
# ---------------------------------------------------------------------------


class TestCategoryOrdering:
    """Ensure HTML categories follow the same ordering as the PDF output."""

    def test_youth_before_adult_women_before_adult_men(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        header = "Name,Club,r1,score\nA,C,1,1"
        _write_csv(scores / "U13B.csv", header)  # youth
        _write_csv(scores / "SW.csv", header)  # adult women
        _write_csv(scores / "SM.csv", header)  # adult men

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        pos_u13b = content.index("Under 13 Boys")
        pos_sw = content.index("Senior Women")
        pos_sm = content.index("Senior Men")

        assert pos_u13b < pos_sw < pos_sm


# ---------------------------------------------------------------------------
# HTML escaping / security
# ---------------------------------------------------------------------------


class TestHtmlEscaping:
    """Verify that user-provided data is HTML-escaped in the output."""

    def test_special_characters_escaped(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        # Athlete name with HTML special characters
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\n<script>alert(1)</script>,C,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        # Raw <script> tag from data must not appear unescaped
        assert "<script>alert(1)</script>" not in content
        # Escaped form must be present instead
        assert "&lt;script&gt;" in content

    def test_ampersand_in_name_escaped(self, tmp_config, tmp_path):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nAlice & Bob,Harriers,1,1")

        output_path = tmp_path / "output" / "results.html"
        generator = HtmlOutputGenerator(config=tmp_config, output_path=output_path)
        generator.generate()

        content = output_path.read_text(encoding="utf-8")
        assert "Alice &amp; Bob" in content


# ---------------------------------------------------------------------------
# Helper method unit tests
# ---------------------------------------------------------------------------


class TestHtmlOutputGeneratorHelpers:
    """Unit tests for internal helper methods."""

    def test_format_cell_integer(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        assert gen._format_cell(3.0) == "3"

    def test_format_cell_string(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        assert gen._format_cell("Alice") == "Alice"

    def test_format_cell_nan(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        assert gen._format_cell(float("nan")) == ""

    def test_round_tooltip_format(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        result = gen._round_tooltip("R 1", ["Alice (3)", "Bob (5)"])
        assert "R 1" in result
        assert "Alice (3)" in result
        assert "Bob (5)" in result

    def test_total_score_tooltip_includes_all_rounds(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        round_runners = {
            "R 1": ["Alice (3)", "Bob (5)"],
            "R 2": ["Alice (2)", "Charlie (4)"],
        }
        result = gen._total_score_tooltip(round_runners)
        assert "R 1" in result
        assert "R 2" in result
        assert "Alice (3)" in result
        assert "Charlie (4)" in result

    def test_total_score_tooltip_empty(self, tmp_config):
        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        assert gen._total_score_tooltip({}) == ""

    def test_make_section_id_alphanumeric(self, tmp_config):
        import pandas as pd

        from pyresults.output.score_data_provider import CategoryDisplayData

        gen = HtmlOutputGenerator(config=tmp_config, output_path=tmp_config.data_base_path)
        data = CategoryDisplayData(
            category_code="U13B",
            title="Under 13 Boys",
            dataframe=pd.DataFrame(),
            is_team=False,
        )
        section_id = gen._make_section_id(data)
        # Section ID must be safe for use as an HTML id attribute (no spaces)
        assert " " not in section_id
        assert re.match(r"^[A-Za-z0-9\-]+$", section_id)
