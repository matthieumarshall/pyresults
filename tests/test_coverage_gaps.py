"""Tests for areas not covered by the existing test suite.

Covers:
- Domain model validation (Athlete, RaceResult, Round, Score, Category, Team)
- CompetitionConfig logic (guests, divisions, club aliases, category mapping)
- RaceProcessorService edge cases (name cleaning, guest filtering, position reset)
- CsvRaceResultRepository / CsvScoreRepository round-trip persistence
- Score edge cases and total calculation
"""

from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from pyresults.config import build_default_config
from pyresults.config.category_config import build_default_categories
from pyresults.domain import (
    Athlete,
    Category,
    CategoryType,
    DomainRaceResult,
    DomainRound,
    Score,
    Team,
)
from pyresults.domain.category import Gender
from pyresults.repositories.csv_race_result_repository import CsvRaceResultRepository
from pyresults.repositories.csv_score_repository import CsvScoreRepository
from pyresults.repositories.interfaces import IRaceResultRepository, IScoreRepository
from pyresults.services.race_processor_service import RaceProcessorService

# ===================================================================
# Domain: Athlete
# ===================================================================


class TestAthleteValidation:
    def test_valid_athlete(self) -> None:
        a = Athlete(
            name="Jane Doe",
            club="Fast Club",
            race_number="42",
            position=1,
            time=timedelta(minutes=20),
            gender="Female",
            category="SW",
        )
        assert a.name == "Jane Doe"
        assert str(a) == "Jane Doe (Fast Club)"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            Athlete(
                name="",
                club="Club",
                race_number="1",
                position=1,
                time=timedelta(minutes=1),
                gender="Male",
                category="SM",
            )

    def test_empty_club_raises(self) -> None:
        with pytest.raises(ValueError, match="club cannot be empty"):
            Athlete(
                name="X",
                club="",
                race_number="1",
                position=1,
                time=timedelta(minutes=1),
                gender="Male",
                category="SM",
            )

    def test_zero_position_raises(self) -> None:
        with pytest.raises(ValueError, match="Position must be positive"):
            Athlete(
                name="X",
                club="C",
                race_number="1",
                position=0,
                time=timedelta(minutes=1),
                gender="Male",
                category="SM",
            )

    def test_negative_position_raises(self) -> None:
        with pytest.raises(ValueError, match="Position must be positive"):
            Athlete(
                name="X",
                club="C",
                race_number="1",
                position=-5,
                time=timedelta(minutes=1),
                gender="Male",
                category="SM",
            )

    def test_is_guest(self) -> None:
        a = Athlete(
            name="Guest Runner",
            club="Visiting Club",
            race_number="1620",
            position=1,
            time=timedelta(minutes=25),
            gender="Male",
            category="SM",
        )
        guests = {"1620", "1621"}
        assert a.is_guest(guests) is True
        assert a.is_guest({"9999"}) is False


# ===================================================================
# Domain: RaceResult
# ===================================================================


class TestRaceResultValidation:
    def test_valid_race_result(self) -> None:
        rr = DomainRaceResult(race_name="Men", round_number="r1")
        assert len(rr) == 0

    def test_empty_race_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Race name cannot be empty"):
            DomainRaceResult(race_name="", round_number="r1")

    def test_empty_round_number_raises(self) -> None:
        with pytest.raises(ValueError, match="Round number cannot be empty"):
            DomainRaceResult(race_name="Men", round_number="")

    def test_add_and_query_athletes(self) -> None:
        rr = DomainRaceResult(race_name="U13", round_number="r1")
        a1 = Athlete("A", "Club X", "1", 1, timedelta(minutes=8), "Male", "U13B")
        a2 = Athlete("B", "Club Y", "2", 2, timedelta(minutes=9), "Female", "U13G")
        a3 = Athlete("C", "Club X", "3", 3, timedelta(minutes=10), "Male", "U13B")
        rr.add_athlete(a1)
        rr.add_athlete(a2)
        rr.add_athlete(a3)

        assert len(rr) == 3
        assert rr.get_athletes_by_category("U13B") == [a1, a3]
        assert rr.get_athletes_by_club("Club X") == [a1, a3]
        assert rr.get_clubs() == {"Club X", "Club Y"}
        assert rr.get_categories() == {"U13B", "U13G"}


# ===================================================================
# Domain: Round
# ===================================================================


class TestRoundValidation:
    def test_empty_round_number_raises(self) -> None:
        with pytest.raises(ValueError, match="Round number cannot be empty"):
            DomainRound(number="")

    def test_add_race_result_wrong_round_raises(self) -> None:
        rnd = DomainRound(number="r1")
        rr = DomainRaceResult(race_name="Men", round_number="r2")
        with pytest.raises(ValueError, match="does not match"):
            rnd.add_race_result(rr)

    def test_add_and_query_race_results(self) -> None:
        rnd = DomainRound(number="r1")
        rr1 = DomainRaceResult(race_name="Men", round_number="r1")
        rr2 = DomainRaceResult(race_name="U13", round_number="r1")
        rnd.add_race_result(rr1)
        rnd.add_race_result(rr2)

        assert len(rnd) == 2
        assert rnd.has_race("Men") is True
        assert rnd.has_race("Women") is False
        assert rnd.get_race_result("U13") is rr2

    def test_get_missing_race_raises(self) -> None:
        rnd = DomainRound(number="r1")
        with pytest.raises(ValueError, match="not found"):
            rnd.get_race_result("NonExistent")


# ===================================================================
# Domain: Score
# ===================================================================


class TestScoreEdgeCases:
    def test_empty_scores_returns_sentinel(self) -> None:
        s = Score(name="Nobody", club="C", category="SM", round_scores={})
        assert s.calculate_total_score(1) == 999999
        assert s.get_rounds_competed() == 0

    def test_one_round_best_of_one(self) -> None:
        s = Score(name="Solo", club="C", category="SM", round_scores={"r1": 5})
        assert s.calculate_total_score(1) == 5

    def test_insufficient_rounds(self) -> None:
        s = Score(name="X", club="C", category="SM", round_scores={"r1": 2})
        assert s.calculate_total_score(2) == 999999

    def test_best_two_of_three(self) -> None:
        s = Score(name="X", club="C", category="SM", round_scores={"r1": 5, "r2": 3, "r3": 10})
        # Best 2 of 3 = 3 + 5 = 8
        assert s.calculate_total_score(2) == 8

    def test_add_round_score_rejects_zero(self) -> None:
        s = Score(name="X", club="C", category="SM", round_scores={})
        with pytest.raises(ValueError, match="Score must be positive"):
            s.add_round_score("r1", 0)

    def test_add_round_score_rejects_negative(self) -> None:
        s = Score(name="X", club="C", category="SM", round_scores={})
        with pytest.raises(ValueError, match="Score must be positive"):
            s.add_round_score("r1", -1)

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            Score(name="", club="C", category="SM", round_scores={})

    def test_empty_category_raises(self) -> None:
        with pytest.raises(ValueError, match="category cannot be empty"):
            Score(name="X", club="C", category="", round_scores={})


# ===================================================================
# Domain: Category
# ===================================================================


class TestCategoryValidation:
    def test_team_category_missing_team_size_raises(self) -> None:
        with pytest.raises(ValueError, match="must have team_size"):
            Category(
                code="X",
                name="Test",
                category_type=CategoryType.TEAM,
                gender=Gender.MALE,
                race_name="U13",
                team_size=None,
            )

    def test_team_category_zero_team_size_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            Category(
                code="X",
                name="Test",
                category_type=CategoryType.TEAM,
                gender=Gender.MALE,
                race_name="U13",
                team_size=0,
            )

    def test_individual_category_no_team_size_ok(self) -> None:
        c = Category(
            code="SM",
            name="Senior Men",
            category_type=CategoryType.INDIVIDUAL,
            gender=Gender.MALE,
            race_name="Men",
        )
        assert c.is_individual_category() is True
        assert c.is_team_category() is False
        assert c.is_overall_category() is False

    def test_overall_category(self) -> None:
        c = Category(
            code="MO",
            name="Mens Overall",
            category_type=CategoryType.OVERALL,
            gender=Gender.MALE,
            race_name="Men",
        )
        assert c.is_overall_category() is True

    def test_empty_code_raises(self) -> None:
        with pytest.raises(ValueError, match="code cannot be empty"):
            Category(
                code="",
                name="Test",
                category_type=CategoryType.INDIVIDUAL,
                gender=Gender.MALE,
                race_name="Men",
            )


# ===================================================================
# Domain: Team
# ===================================================================


class TestTeamValidation:
    def test_empty_club_raises(self) -> None:
        with pytest.raises(ValueError, match="club cannot be empty"):
            Team(club="", category="U13B")

    def test_empty_category_raises(self) -> None:
        with pytest.raises(ValueError, match="category cannot be empty"):
            Team(club="Club A", category="")

    def test_add_wrong_club_athlete_raises(self) -> None:
        t = Team(club="Club A", category="U13B")
        a = Athlete("X", "Club B", "1", 1, timedelta(minutes=8), "Male", "U13B")
        with pytest.raises(ValueError, match="does not match"):
            t.add_athlete(a)

    def test_name_includes_label(self) -> None:
        t = Team(club="Oxford AC", category="U13B", label="B")
        assert t.name == "Oxford AC B"


# ===================================================================
# CompetitionConfig
# ===================================================================


class TestCompetitionConfig:
    def test_is_guest(self) -> None:
        config = build_default_config()
        # 1611 is a guest
        assert config.is_guest("1611") is True
        # 1615-1657 are guests
        assert config.is_guest("1615") is True
        assert config.is_guest("1657") is True
        # Normal numbers are not guests
        assert config.is_guest("100") is False
        assert config.is_guest("1614") is False

    def test_get_division_known_clubs(self) -> None:
        config = build_default_config()
        assert config.get_division("Abingdon AC", "Male") == "1"
        assert config.get_division("Alchester Running Club", "Male") == "2"
        assert config.get_division("Headington RR", "Female") == "1"
        assert config.get_division("Didcot Runners", "Female") == "2"

    def test_get_division_unknown_club_defaults_to_3(self) -> None:
        config = build_default_config()
        assert config.get_division("Unknown Club", "Male") == "3"
        assert config.get_division("Unknown Club", "Female") == "3"

    def test_normalize_club_name_alias(self) -> None:
        config = build_default_config()
        assert config.normalize_club_name("Radley AC") == "Radley Athletic Club"

    def test_normalize_club_name_no_alias(self) -> None:
        config = build_default_config()
        assert config.normalize_club_name("Oxford City AC") == "Oxford City AC"

    def test_map_category_valid(self) -> None:
        config = build_default_config()
        assert config.map_category("Male", "Senior Men") == "SM"
        assert config.map_category("Female", "V40") == "WV40"
        assert config.map_category("Male", "U13 Boys") == "U13B"

    def test_map_category_strips_whitespace(self) -> None:
        config = build_default_config()
        # Input data sometimes has trailing spaces
        assert config.map_category(" Male ", " U13 Boys ") == "U13B"

    def test_map_category_unknown_raises(self) -> None:
        config = build_default_config()
        with pytest.raises(ValueError, match="No category mapping"):
            config.map_category("Male", "Nonexistent Category")

    def test_get_gender_for_race(self) -> None:
        config = build_default_config()
        assert config.get_gender_for_race("Men") == "Male"
        assert config.get_gender_for_race("Women") == "Female"

    def test_get_gender_for_unknown_race_raises(self) -> None:
        config = build_default_config()
        with pytest.raises(ValueError, match="No gender mapping"):
            config.get_gender_for_race("UnknownRace")


# ===================================================================
# CategoryConfig
# ===================================================================


class TestCategoryConfig:
    def test_get_unknown_category_raises(self) -> None:
        cat_config = build_default_categories()
        with pytest.raises(ValueError, match="Unknown category"):
            cat_config.get_category("NOPE")

    def test_get_all_categories_not_empty(self) -> None:
        cat_config = build_default_categories()
        all_cats = cat_config.get_all_categories()
        assert len(all_cats) > 10  # We know there are ~24 categories

    def test_get_team_size_for_youth(self) -> None:
        cat_config = build_default_categories()
        assert cat_config.get_team_size_for_category("U13B") == 3

    def test_get_team_size_for_men(self) -> None:
        cat_config = build_default_categories()
        assert cat_config.get_team_size_for_category("Men") == 7

    def test_get_team_size_for_women(self) -> None:
        cat_config = build_default_categories()
        assert cat_config.get_team_size_for_category("Women") == 4

    def test_get_team_size_for_individual_raises(self) -> None:
        cat_config = build_default_categories()
        with pytest.raises(ValueError, match="not a team category"):
            cat_config.get_team_size_for_category("SM")

    def test_categories_by_type(self) -> None:
        cat_config = build_default_categories()
        individuals = cat_config.get_categories_by_type(CategoryType.INDIVIDUAL)
        teams = cat_config.get_categories_by_type(CategoryType.TEAM)
        overalls = cat_config.get_categories_by_type(CategoryType.OVERALL)

        assert len(individuals) > 0
        assert len(teams) > 0
        assert len(overalls) == 2  # MensOverall, WomensOverall

        assert all(c.is_individual_category() for c in individuals)
        assert all(c.is_team_category() for c in teams)
        assert all(c.is_overall_category() for c in overalls)

    def test_race_name_for_category(self) -> None:
        cat_config = build_default_categories()
        assert cat_config.get_race_name_for_category("U13B") == "U13"
        assert cat_config.get_race_name_for_category("SM") == "Men"
        assert cat_config.get_race_name_for_category("MensOverall") == "Men"


# ===================================================================
# RaceProcessorService: name cleaning, guest filtering, position reset
# ===================================================================


class TestRaceProcessorNameCleaning:
    """Unit tests for RaceProcessorService._clean_name."""

    def _make_service(self) -> RaceProcessorService:
        config = build_default_config()
        repo = CsvRaceResultRepository(base_path=Path("."))
        return RaceProcessorService(config=config, repository=repo)

    def test_strips_whitespace(self) -> None:
        s = self._make_service()
        assert s._clean_name("  John Smith  ") == "John Smith"

    def test_collapses_multiple_spaces(self) -> None:
        s = self._make_service()
        assert s._clean_name("John    Smith") == "John Smith"

    def test_handles_nan(self) -> None:
        s = self._make_service()
        assert s._clean_name(float("nan")) == ""

    def test_normal_name_unchanged(self) -> None:
        s = self._make_service()
        assert s._clean_name("Alice Brown") == "Alice Brown"


class TestRaceProcessorGuestFiltering:
    """Guest athletes should be removed and positions renumbered."""

    def test_guests_filtered_and_positions_reset(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        # Create input with a guest (race number 1620 is in range 1615-1657)
        csv_content = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,100,Normal Runner,00:30:00,Senior Men,1,Male,1,Club A
2,1620,Guest Runner,00:30:30,Senior Men,2,Male,2,Visiting Club
3,200,Another Runner,00:31:00,Senior Men,3,Male,3,Club B
"""
        input_file = tmp_path / "input_data" / "r1" / "Men.csv"
        input_file.parent.mkdir(parents=True)
        input_file.write_text(csv_content, encoding="utf-16")

        race_result = service.process_race_file(input_file)

        # Guest should be filtered out
        assert len(race_result.athletes) == 2
        names = [a.name for a in race_result.athletes]
        assert "Guest Runner" not in names

        # Positions should be sequential after filtering
        positions = [a.position for a in race_result.athletes]
        assert positions == [1, 2]

    def test_no_guests_leaves_data_unchanged(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        csv_content = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,100,Runner A,00:30:00,Senior Men,1,Male,1,Club A
2,200,Runner B,00:31:00,Senior Men,2,Male,2,Club B
"""
        input_file = tmp_path / "input_data" / "r1" / "Men.csv"
        input_file.parent.mkdir(parents=True)
        input_file.write_text(csv_content, encoding="utf-16")

        race_result = service.process_race_file(input_file)
        assert len(race_result.athletes) == 2
        assert [a.position for a in race_result.athletes] == [1, 2]


class TestRaceProcessorClubAliases:
    """Club aliases should be applied during processing."""

    def test_club_alias_normalized(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        csv_content = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,100,Runner A,00:30:00,Senior Men,1,Male,1,Radley AC
2,200,Runner B,00:31:00,Senior Men,2,Male,2,Radley Athletic Club
"""
        input_file = tmp_path / "input_data" / "r1" / "Men.csv"
        input_file.parent.mkdir(parents=True)
        input_file.write_text(csv_content, encoding="utf-16")

        race_result = service.process_race_file(input_file)
        clubs = {a.club for a in race_result.athletes}
        # Both should be normalized to the canonical name
        assert clubs == {"Radley Athletic Club"}


class TestRaceProcessorCategoryMapping:
    """Categories from the raw CSV should be mapped to standard codes."""

    def test_mixed_gender_youth_race_maps_categories(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        csv_content = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,301,Boy Runner,00:08:10,U13 Boys,1,Male,1,Club A
2,302,Girl Runner,00:08:30,U13 Girls,1,Female,1,Club B
"""
        input_file = tmp_path / "input_data" / "r1" / "U13.csv"
        input_file.parent.mkdir(parents=True)
        input_file.write_text(csv_content, encoding="utf-16")

        race_result = service.process_race_file(input_file)
        categories = {a.category for a in race_result.athletes}
        assert "U13B" in categories
        assert "U13G" in categories


# ===================================================================
# CsvRaceResultRepository: round-trip persistence
# ===================================================================


class TestCsvRaceResultRepository:
    def test_save_and_load_round_trip(self, tmp_path) -> None:
        repo = CsvRaceResultRepository(base_path=tmp_path)

        rr = DomainRaceResult(race_name="Men", round_number="r1")
        rr.add_athlete(
            Athlete("John Doe", "Fast Club", "42", 1, timedelta(minutes=30), "Male", "SM")
        )
        rr.add_athlete(
            Athlete("Jane Roe", "Slow Club", "43", 2, timedelta(minutes=32), "Female", "SW")
        )

        repo.save_race_result(rr)
        assert repo.exists("Men", "r1")

        loaded = repo.load_race_result("Men", "r1")
        assert loaded is not None
        assert len(loaded.athletes) == 2
        assert loaded.athletes[0].name == "John Doe"
        assert loaded.athletes[1].position == 2

    def test_load_nonexistent_returns_none(self, tmp_path) -> None:
        repo = CsvRaceResultRepository(base_path=tmp_path)
        assert repo.exists("Men", "r99") is False
        assert repo.load_race_result("Men", "r99") is None

    def test_get_available_races(self, tmp_path) -> None:
        repo = CsvRaceResultRepository(base_path=tmp_path)

        # Create some race files
        rr1 = DomainRaceResult(race_name="Men", round_number="r1")
        rr1.add_athlete(Athlete("A", "C", "1", 1, timedelta(minutes=30), "Male", "SM"))
        rr2 = DomainRaceResult(race_name="U13", round_number="r1")
        rr2.add_athlete(Athlete("B", "C", "2", 1, timedelta(minutes=8), "Male", "U13B"))
        repo.save_race_result(rr1)
        repo.save_race_result(rr2)

        races = repo.get_available_races("r1")
        assert sorted(races) == ["Men", "U13"]

    def test_get_available_races_missing_dir(self, tmp_path) -> None:
        repo = CsvRaceResultRepository(base_path=tmp_path)
        assert repo.get_available_races("r99") == []


# ===================================================================
# CsvScoreRepository: round-trip persistence
# ===================================================================


class TestCsvScoreRepository:
    def test_save_and_load_round_trip(self, tmp_path) -> None:
        repo = CsvScoreRepository(base_path=tmp_path, round_numbers=["r1", "r2", "r3"])

        scores = [
            Score(name="Alice", club="Club A", category="U13B", round_scores={"r1": 1, "r2": 3}),
            Score(name="Bob", club="Club B", category="U13B", round_scores={"r1": 2}),
        ]
        repo.save_scores("U13B", scores)
        assert repo.exists("U13B")

        loaded = repo.load_scores("U13B")
        assert len(loaded) == 2
        assert loaded[0].name == "Alice"
        assert loaded[0].round_scores == {"r1": 1, "r2": 3}
        assert loaded[1].name == "Bob"
        assert loaded[1].round_scores == {"r1": 2}

    def test_load_nonexistent_returns_empty(self, tmp_path) -> None:
        repo = CsvScoreRepository(base_path=tmp_path, round_numbers=["r1"])
        assert repo.exists("NOPE") is False
        assert repo.load_scores("NOPE") == []

    def test_score_column_empty_for_insufficient_rounds(self, tmp_path) -> None:
        """An athlete with only 1 round when best-2-of-3 applies should have
        an empty score column in the CSV."""
        repo = CsvScoreRepository(base_path=tmp_path, round_numbers=["r1", "r2", "r3"])

        scores = [
            Score(name="Full", club="C", category="SM", round_scores={"r1": 5, "r2": 3, "r3": 4}),
            Score(name="Partial", club="C", category="SM", round_scores={"r1": 5}),
        ]
        repo.save_scores("SM", scores)

        df = pd.read_csv(tmp_path / "SM.csv")
        # 3 rounds available → rounds_to_count = 2 (best 2 of 3)
        # "Full" should have a score (best 2 of 3 = 3+4 = 7)
        full_score = df.loc[df["Name"] == "Full", "score"].values[0]
        assert int(full_score) == 7
        # "Partial" has only 1 round, needs 2 → empty score
        partial_score = df.loc[df["Name"] == "Partial", "score"].values[0]
        assert pd.isna(partial_score) or str(partial_score).strip() == ""


# ===================================================================
# RaceProcessorService: UTF-16 file reading
# ===================================================================


class TestRaceFileReading:
    def test_reads_utf16_comma_separated(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        csv_content = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,100,Runner A,00:30:00,Senior Men,1,Male,1,Club A
"""
        input_file = tmp_path / "test.csv"
        input_file.write_text(csv_content, encoding="utf-16")

        df = service._read_race_file(input_file)
        assert "Race No" in df.columns
        assert len(df) == 1

    def test_reads_utf16_tab_separated(self, tmp_path) -> None:
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        repo = CsvRaceResultRepository(base_path=config.data_base_path)
        service = RaceProcessorService(config=config, repository=repo)

        # Tab-separated content
        tsv_content = (
            "Pos\tRace No\tName\tTime\tCategory\tCat Pos\tGender\tGen Pos\tClub\n"
            "1\t100\tRunner A\t00:30:00\tSenior Men\t1\tMale\t1\tClub A\n"
        )
        input_file = tmp_path / "test.csv"
        input_file.write_text(tsv_content, encoding="utf-16")

        df = service._read_race_file(input_file)
        assert "Race No" in df.columns
        assert len(df) == 1


# ===================================================================
# Edge case: single round uses all rounds (no drop)
# ===================================================================


class TestSingleRoundScoring:
    """With only 1 round, best-N-of-N means all rounds count (no drop)."""

    def test_single_round_no_drop(self) -> None:
        config = build_default_config()
        config.round_numbers = ["r1"]

        race_results = {
            ("U13", "r1"): _build_race_result(
                [
                    (1, "Alice", "Club A", "U13B"),
                    (2, "Bob", "Club B", "U13B"),
                ],
            ),
        }
        race_repo = _InMemoryRaceRepo(race_results)
        score_repo = _InMemoryScoreRepo()

        from pyresults.services import IndividualScoreService

        service = IndividualScoreService(
            config=config, race_result_repo=race_repo, score_repo=score_repo
        )
        service.update_scores_for_category("U13B")

        saved = score_repo.saved_scores["U13B"]
        by_name = {s.name: s for s in saved}
        # With 1 round, rounds_to_count = 1, so the score is the position
        assert by_name["Alice"].calculate_total_score(1) == 1
        assert by_name["Bob"].calculate_total_score(1) == 2


# Minimal in-memory stubs for single-round test
class _InMemoryRaceRepo(IRaceResultRepository):
    def __init__(self, results):
        self._results = results

    def load_race_result(self, race_name, round_number):
        return self._results.get((race_name, round_number))

    def save_race_result(self, race_result):
        pass

    def exists(self, race_name, round_number):
        return (race_name, round_number) in self._results

    def get_available_races(self, round_number):
        return [r for r, rn in self._results if rn == round_number]


class _InMemoryScoreRepo(IScoreRepository):
    def __init__(self):
        self.saved_scores = {}

    def load_scores(self, category):
        return self.saved_scores.get(category, [])

    def save_scores(self, category, scores):
        self.saved_scores[category] = list(scores)

    def exists(self, category):
        return category in self.saved_scores


def _build_race_result(placements):
    result = DomainRaceResult(race_name="U13", round_number="r1")
    for position, name, club, category in placements:
        result.add_athlete(
            Athlete(
                name,
                club,
                str(100 + position),
                position,
                timedelta(minutes=8, seconds=position),
                "Male",
                category,
            )
        )
    return result
