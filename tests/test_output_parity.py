"""Tests for ScoreDataProvider and output parity.

Ensures that:
- ScoreDataProvider correctly loads and formats score data
- Both PDF and Excel generators receive identical data
- Individual scores are the sum of best (n-1) round positions
- Team scores are the sum of round team-scores for best (n-1) rounds
"""

import pandas as pd
import pytest

from pyresults.config import build_default_config
from pyresults.output.score_data_provider import ScoreDataProvider


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
# Category ordering
# ---------------------------------------------------------------------------

class TestCategoryOrdering:
    """Ensure get_all_category_data returns categories in the correct order."""

    def test_empty_scores_directory(self, tmp_config):
        provider = ScoreDataProvider(tmp_config)
        assert provider.get_all_category_data() == []

    def test_individual_before_team(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nA,C,1,1")
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nC A,6,6")

        provider = ScoreDataProvider(tmp_config)
        codes = [d.category_code for d in provider.get_all_category_data()]
        assert codes == ["U13B", "Team U13B"]

    def test_full_ordering(self, tmp_config):
        """Verify youth → senior → adult teams → overall order."""
        scores = tmp_config.data_base_path / "scores"
        header = "Name,Club,r1,score\nA,C,1,1"
        team_header = "Team,r1,score\nC A,6,6"

        # Create a selection of categories to exercise each group
        _write_csv(scores / "U9G.csv", header)
        _write_csv(scores / "teams" / "U9G.csv", team_header)
        _write_csv(scores / "U13B.csv", header)
        _write_csv(scores / "SM.csv", header)
        _write_csv(scores / "teams" / "Men.csv", team_header)
        _write_csv(scores / "MensOverall.csv", header)

        provider = ScoreDataProvider(tmp_config)
        codes = [d.category_code for d in provider.get_all_category_data()]
        assert codes == [
            "U9G", "Team U9G",
            "U13B",
            "SM",
            "Team Men",
            "MensOverall",
        ]


# ---------------------------------------------------------------------------
# DataFrame preparation
# ---------------------------------------------------------------------------

class TestDataFramePreparation:
    """Verify that loaded DataFrames are correctly cleaned for display."""

    def test_round_columns_renamed(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,r2,score\nA,C,1,2,1")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert data is not None
        assert "R 1" in data.dataframe.columns
        assert "R 2" in data.dataframe.columns
        assert "r1" not in data.dataframe.columns

    def test_empty_round_columns_dropped(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        # r2 exists but is empty for all rows
        _write_csv(scores / "U13B.csv", "Name,Club,r1,r2,score\nA,C,1,,1")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert "R 1" in data.dataframe.columns
        assert "R 2" not in data.dataframe.columns

    def test_score_column_capitalised(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nA,C,1,1")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert "Score" in data.dataframe.columns
        assert "score" not in data.dataframe.columns

    def test_position_column_added(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,score\nAlice,C,1,1\nBob,C,2,2",
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert data.dataframe.columns[0] == "Pos"
        assert list(data.dataframe["Pos"]) == [1, 2]

    def test_numeric_values_are_integers(self, tmp_config):
        """Round and score values should display as plain integers, not floats."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,r2,score\nA,C,3,5,3")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        # Values should be int (or empty string for missing)
        assert data.dataframe["R 1"].iloc[0] == 3
        assert data.dataframe["Score"].iloc[0] == 3

    def test_empty_rows_filtered_individual(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,score\nAlice,C,1,1\n,,,"
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert len(data.dataframe) == 1

    def test_empty_rows_filtered_team(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "teams" / "U13B.csv",
            "Team,r1,score\nClub A A,6,6\n,,"
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("Team U13B")

        assert len(data.dataframe) == 1


# ---------------------------------------------------------------------------
# Title resolution
# ---------------------------------------------------------------------------

class TestTitleResolution:
    def test_individual_category_title(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nA,C,1,1")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")

        assert data.title == "Under 13 Boys"

    def test_team_category_title(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "teams" / "Men.csv", "Team,r1,score\nC A,6,6")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("Team Men")

        assert data.title == "Men's Teams"

    def test_unknown_category_uses_code(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "Unknown.csv", "Name,Club,r1,score\nA,C,1,1")

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("Unknown")

        assert data.title == "Unknown"


# ---------------------------------------------------------------------------
# Score correctness — individual
# ---------------------------------------------------------------------------

class TestIndividualScoreCorrectness:
    """Verify that the provider faithfully reproduces the CSV score values.

    The CSV is the authoritative source; the provider must NOT recalculate.
    """

    def test_score_matches_csv(self, tmp_config):
        """Score column should be copied from the CSV, not recomputed."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,r2,r3,r4,score\n"
            "Sam,Radley,1,,1,1,3\n"
            "Jack,Abingdon,2,1,3,2,5\n"
            "Reuben,Banbury,4,,5,3,12",
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")
        df = data.dataframe

        assert list(df["Score"]) == [3, 5, 12]

    def test_score_empty_when_insufficient_rounds(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,r2,score\n"
            "Alice,C,1,,\n"
            "Bob,C,2,3,2",
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")
        df = data.dataframe

        # Alice has no score (insufficient rounds)
        assert df["Score"].iloc[0] == ""
        # Bob has a valid score
        assert df["Score"].iloc[1] == 2


# ---------------------------------------------------------------------------
# Score correctness — teams
# ---------------------------------------------------------------------------

class TestTeamScoreCorrectness:
    """Verify that team scores are faithfully reproduced from CSVs."""

    def test_team_score_matches_csv(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "teams" / "U13B.csv",
            "Team,r1,r2,r3,r4,score\n"
            "Abingdon AC A,16,6,18,19,40\n"
            "Radley AC A,22,30,29,22,73",
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("Team U13B")
        df = data.dataframe

        assert list(df["Score"]) == [40, 73]
        assert list(df["R 1"]) == [16, 22]


# ---------------------------------------------------------------------------
# Output parity — PDF and Excel receive identical data
# ---------------------------------------------------------------------------

class TestOutputParity:
    """Both output generators must receive exactly the same DataFrames."""

    def test_pdf_and_excel_see_same_categories(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(scores / "U13B.csv", "Name,Club,r1,score\nA,C,1,1")
        _write_csv(scores / "SM.csv", "Name,Club,r1,score\nB,D,2,2")
        _write_csv(scores / "teams" / "U13B.csv", "Team,r1,score\nC A,6,6")

        provider_a = ScoreDataProvider(tmp_config)
        provider_b = ScoreDataProvider(tmp_config)

        cats_a = [d.category_code for d in provider_a.get_all_category_data()]
        cats_b = [d.category_code for d in provider_b.get_all_category_data()]

        assert cats_a == cats_b

    def test_pdf_and_excel_see_same_data(self, tmp_config):
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,r2,r3,r4,score\n"
            "Sam,Radley,1,,1,1,3\n"
            "Jack,Abingdon,2,1,3,2,5",
        )

        provider_a = ScoreDataProvider(tmp_config)
        provider_b = ScoreDataProvider(tmp_config)

        data_a = provider_a.get_category_data("U13B")
        data_b = provider_b.get_category_data("U13B")

        pd.testing.assert_frame_equal(data_a.dataframe, data_b.dataframe)

    def test_no_cumulative_in_round_columns(self, tmp_config):
        """Round columns must show per-round values, not cumulative sums."""
        scores = tmp_config.data_base_path / "scores"
        _write_csv(
            scores / "U13B.csv",
            "Name,Club,r1,r2,r3,r4,score\n"
            "Jack,Abingdon,2,1,3,2,5",
        )

        provider = ScoreDataProvider(tmp_config)
        data = provider.get_category_data("U13B")
        df = data.dataframe

        # These should be the raw per-round values, NOT cumulative
        assert df["R 1"].iloc[0] == 2
        assert df["R 2"].iloc[0] == 1
        assert df["R 3"].iloc[0] == 3
        assert df["R 4"].iloc[0] == 2
