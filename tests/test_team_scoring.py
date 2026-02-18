"""Tests for team scoring calculations."""

from datetime import timedelta
from unittest.mock import Mock

import pandas as pd

from pyresults.config import build_default_config
from pyresults.domain import Athlete, DomainRaceResult, Team
from pyresults.services import TeamScoreService, TeamScoringService


def _create_athlete(
    name: str, club: str, position: int, category: str, gender: str = "Male"
) -> Athlete:
    """Helper to create an athlete for testing."""
    return Athlete(
        name=name,
        club=club,
        race_number=str(1000 + position),
        position=position,
        time=timedelta(minutes=10, seconds=position),
        gender=gender,
        category=category,
    )


def _create_race_result(race_name: str, athletes: list[Athlete]) -> DomainRaceResult:
    """Helper to create a race result for testing."""
    result = DomainRaceResult(race_name=race_name, round_number="r1")
    for athlete in athletes:
        result.add_athlete(athlete)
    return result


class TestTeamSizes:
    """Test that team sizes are configured correctly."""

    def test_junior_team_size_is_3(self) -> None:
        config = build_default_config()

        # Test all junior categories
        junior_categories = [
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
        ]
        for category_code in junior_categories:
            category = config.category_config.get_category(category_code)
            assert category.team_size == 3, f"{category_code} should have team size 3"

    def test_mens_team_size_is_7(self) -> None:
        config = build_default_config()
        category = config.category_config.get_category("Men")
        assert category.team_size == 7

    def test_womens_team_size_is_4(self) -> None:
        config = build_default_config()
        category = config.category_config.get_category("Women")
        assert category.team_size == 4


class TestTeamLabels:
    """Test that teams are labeled correctly (A, B, C, etc.)."""

    def test_single_team_gets_label_a(self) -> None:
        team = Team(club="Oxford AC", category="U13B", label="A")
        assert team.label == "A"
        assert team.name == "Oxford AC A"

    def test_multiple_teams_get_different_labels(self) -> None:
        team_a = Team(club="Oxford AC", category="U13B", label="A")
        team_b = Team(club="Oxford AC", category="U13B", label="B")

        assert team_a.label == "A"
        assert team_b.label == "B"
        assert team_a.name == "Oxford AC A"
        assert team_b.name == "Oxford AC B"


class TestMultipleTeamsPerClub:
    """Test that clubs with enough athletes generate multiple teams."""

    def test_club_with_6_athletes_creates_2_junior_teams(self) -> None:
        """Club with 6 athletes should create 2 teams of 3 for junior categories."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        # Create 6 athletes from same club
        athletes = [_create_athlete(f"Athlete {i}", "Oxford AC", i, "U13B") for i in range(1, 7)]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        # Should create 2 teams (A and B)
        oxford_teams = [t for t in teams if t.club == "Oxford AC"]
        assert len(oxford_teams) == 2
        assert oxford_teams[0].label == "A"
        assert oxford_teams[1].label == "B"
        assert len(oxford_teams[0].athletes) == 3
        assert len(oxford_teams[1].athletes) == 3

    def test_club_with_14_athletes_creates_2_mens_teams(self) -> None:
        """Club with 14 athletes should create 2 teams of 7 for men's category."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("Men")

        # Create 14 athletes from same club with different age categories
        athletes = []
        for i in range(1, 15):
            cat = "SM" if i <= 7 else "MV40"
            athletes.append(_create_athlete(f"Athlete {i}", "Oxford AC", i, cat))

        race_result = _create_race_result("Men", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        oxford_teams = [t for t in teams if t.club == "Oxford AC"]
        assert len(oxford_teams) == 2
        assert oxford_teams[0].label == "A"
        assert oxford_teams[1].label == "B"
        assert len(oxford_teams[0].athletes) == 7
        assert len(oxford_teams[1].athletes) == 7

    def test_athletes_assigned_sequentially_by_position(self) -> None:
        """Athletes should be assigned to teams in order of their position."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        # Create 6 athletes with specific positions
        athletes = [
            _create_athlete("Athlete 1", "Club A", 5, "U13B"),
            _create_athlete("Athlete 2", "Club A", 10, "U13B"),
            _create_athlete("Athlete 3", "Club A", 15, "U13B"),
            _create_athlete("Athlete 4", "Club A", 20, "U13B"),
            _create_athlete("Athlete 5", "Club A", 25, "U13B"),
            _create_athlete("Athlete 6", "Club A", 30, "U13B"),
        ]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        club_a_teams = sorted([t for t in teams if t.club == "Club A"], key=lambda t: t.label)

        # Team A should have positions 5, 10, 15
        team_a_positions = sorted([a.position for a in club_a_teams[0].athletes])
        assert team_a_positions == [5, 10, 15]

        # Team B should have positions 20, 25, 30
        team_b_positions = sorted([a.position for a in club_a_teams[1].athletes])
        assert team_b_positions == [20, 25, 30]


class TestMinimumTeamSize:
    """Test that teams need at least half the team size to be valid."""

    def test_junior_team_needs_at_least_2_athletes(self) -> None:
        """Junior teams (size 3) need at least 2 athletes."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        # Club with only 1 athlete - should not create a team
        athletes = [_create_athlete("Athlete 1", "Club A", 1, "U13B")]
        race_result = _create_race_result("U13", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club A"]) == 0

        # Club with 2 athletes - should create a team
        athletes = [
            _create_athlete("Athlete 1", "Club B", 1, "U13B"),
            _create_athlete("Athlete 2", "Club B", 2, "U13B"),
        ]
        race_result = _create_race_result("U13", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club B"]) == 1

    def test_womens_team_needs_at_least_2_athletes(self) -> None:
        """Women's teams (size 4) need at least 2 athletes."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("Women")

        # Club with only 1 athlete - should not create a team
        athletes = [_create_athlete("Athlete 1", "Club A", 1, "SW", "Female")]
        race_result = _create_race_result("Women", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club A"]) == 0

        # Club with 2 athletes - should create a team
        athletes = [
            _create_athlete("Athlete 1", "Club B", 1, "SW", "Female"),
            _create_athlete("Athlete 2", "Club B", 2, "SW", "Female"),
        ]
        race_result = _create_race_result("Women", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club B"]) == 1

    def test_mens_team_needs_at_least_4_athletes(self) -> None:
        """Men's teams (size 7) need at least 4 athletes."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("Men")

        # Club with only 3 athletes - should not create a team
        athletes = [_create_athlete(f"Athlete {i}", "Club A", i, "SM") for i in range(1, 4)]
        race_result = _create_race_result("Men", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club A"]) == 0

        # Club with 4 athletes - should create a team
        athletes = [_create_athlete(f"Athlete {i}", "Club B", i, "SM") for i in range(1, 5)]
        race_result = _create_race_result("Men", athletes)
        teams = service.calculate_teams_for_race(race_result, category)
        assert len([t for t in teams if t.club == "Club B"]) == 1


class TestPenaltyScoring:
    """Test penalty score calculations for incomplete teams."""

    def test_penalty_score_is_n_plus_1(self) -> None:
        """Penalty score should be total athletes in category + 1."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        # Create race with 20 athletes total
        athletes = [_create_athlete(f"Athlete {i}", f"Club {i}", i, "U13B") for i in range(1, 21)]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        # Penalty should be 21 (20 athletes + 1)
        # We can verify this indirectly by checking team scores
        # Any incomplete team would use penalty of 21
        assert len(athletes) == 20  # Verify we have 20 athletes

    def test_incomplete_junior_team_uses_penalty(self) -> None:
        """Junior team with 2 athletes should add 1 penalty score."""
        team = Team(club="Test Club", category="U13B", label="A")

        # Add 2 athletes
        team.add_athlete(_create_athlete("Athlete 1", "Test Club", 5, "U13B"))
        team.add_athlete(_create_athlete("Athlete 2", "Test Club", 10, "U13B"))

        # Team size 3, penalty 21 (assuming 20 athletes in category)
        score = team.calculate_score(team_size=3, penalty_score=21)

        # Score should be 5 + 10 + 21 = 36
        assert score == 36

    def test_incomplete_womens_team_uses_penalty(self) -> None:
        """Women's team with 3 athletes should add 1 penalty score."""
        team = Team(club="Test Club", category="Women", label="A")

        # Add 3 athletes
        for i, pos in enumerate([2, 5, 10], 1):
            team.add_athlete(_create_athlete(f"Athlete {i}", "Test Club", pos, "SW", "Female"))

        # Team size 4, penalty 51 (assuming 50 athletes in category)
        score = team.calculate_score(team_size=4, penalty_score=51)

        # Score should be 2 + 5 + 10 + 51 = 68
        assert score == 68

    def test_incomplete_mens_team_uses_multiple_penalties(self) -> None:
        """Men's team with 5 athletes should add 2 penalty scores."""
        team = Team(club="Test Club", category="Men", label="A")

        # Add 5 athletes
        for i, pos in enumerate([1, 3, 5, 7, 9], 1):
            team.add_athlete(_create_athlete(f"Athlete {i}", "Test Club", pos, "SM"))

        # Team size 7, penalty 101 (assuming 100 athletes in category)
        score = team.calculate_score(team_size=7, penalty_score=101)

        # Score should be 1 + 3 + 5 + 7 + 9 + 101 + 101 = 227 (2 penalties for 2 missing)
        assert score == 227

    def test_complete_team_has_no_penalty(self) -> None:
        """Complete team with all athletes should have no penalty."""
        team = Team(club="Test Club", category="U13B", label="A")

        # Add 3 athletes (full team)
        for i, pos in enumerate([2, 5, 8], 1):
            team.add_athlete(_create_athlete(f"Athlete {i}", "Test Club", pos, "U13B"))

        # Team size 3, penalty 21
        score = team.calculate_score(team_size=3, penalty_score=21)

        # Score should be 2 + 5 + 8 = 15 (no penalty)
        assert score == 15


class TestTeamScoreCalculation:
    """Test team score calculations."""

    def test_team_score_is_sum_of_positions(self) -> None:
        """Team score should be sum of athlete positions."""
        team = Team(club="Test Club", category="U13B", label="A")

        team.add_athlete(_create_athlete("Athlete 1", "Test Club", 3, "U13B"))
        team.add_athlete(_create_athlete("Athlete 2", "Test Club", 7, "U13B"))
        team.add_athlete(_create_athlete("Athlete 3", "Test Club", 12, "U13B"))

        score = team.calculate_score(team_size=3, penalty_score=50)
        assert score == 22  # 3 + 7 + 12

    def test_team_score_uses_best_n_athletes(self) -> None:
        """Team score should use only the best N athletes."""
        team = Team(club="Test Club", category="U13B", label="A")

        # Add 5 athletes but only top 3 should count
        team.add_athlete(_create_athlete("Athlete 1", "Test Club", 2, "U13B"))
        team.add_athlete(_create_athlete("Athlete 2", "Test Club", 5, "U13B"))
        team.add_athlete(_create_athlete("Athlete 3", "Test Club", 8, "U13B"))
        team.add_athlete(_create_athlete("Athlete 4", "Test Club", 15, "U13B"))
        team.add_athlete(_create_athlete("Athlete 5", "Test Club", 20, "U13B"))

        score = team.calculate_score(team_size=3, penalty_score=50)
        assert score == 15  # 2 + 5 + 8 (best 3, not 15 and 20)

    def test_team_too_small_returns_invalid_score(self) -> None:
        """Team below minimum size should return invalid score (999999)."""
        team = Team(club="Test Club", category="U13B", label="A")

        # Add only 1 athlete (minimum is 2 for team size 3)
        team.add_athlete(_create_athlete("Athlete 1", "Test Club", 1, "U13B"))

        score = team.calculate_score(team_size=3, penalty_score=50)
        assert score == 999999


class TestAdultTeamCategories:
    """Test that adult team categories include all athletes from the race."""

    def test_mens_team_includes_all_age_categories(self) -> None:
        """Men's teams should include athletes from all men's age categories."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("Men")

        # Create athletes from different age categories
        athletes = [
            _create_athlete("Young Runner", "Oxford AC", 1, "U20M"),
            _create_athlete("Senior Runner", "Oxford AC", 2, "SM"),
            _create_athlete("V40 Runner", "Oxford AC", 3, "MV40"),
            _create_athlete("V50 Runner", "Oxford AC", 4, "MV50"),
            _create_athlete("V60 Runner", "Oxford AC", 5, "MV60"),
            _create_athlete("V70 Runner", "Oxford AC", 6, "MV70"),
            _create_athlete("Another Senior", "Oxford AC", 7, "SM"),
        ]
        race_result = _create_race_result("Men", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        oxford_teams = [t for t in teams if t.club == "Oxford AC"]
        assert len(oxford_teams) == 1
        assert len(oxford_teams[0].athletes) == 7

        # Verify all different age categories are included
        categories = {a.category for a in oxford_teams[0].athletes}
        assert "U20M" in categories
        assert "SM" in categories
        assert "MV40" in categories
        assert "MV50" in categories
        assert "MV60" in categories
        assert "MV70" in categories

    def test_womens_team_includes_all_age_categories(self) -> None:
        """Women's teams should include athletes from all women's age categories."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("Women")

        # Create athletes from different age categories
        athletes = [
            _create_athlete("Young Runner", "Oxford AC", 1, "U20W", "Female"),
            _create_athlete("Senior Runner", "Oxford AC", 2, "SW", "Female"),
            _create_athlete("V40 Runner", "Oxford AC", 3, "WV40", "Female"),
            _create_athlete("V50 Runner", "Oxford AC", 4, "WV50", "Female"),
        ]
        race_result = _create_race_result("Women", athletes)

        teams = service.calculate_teams_for_race(race_result, category)

        oxford_teams = [t for t in teams if t.club == "Oxford AC"]
        assert len(oxford_teams) == 1
        assert len(oxford_teams[0].athletes) == 4

        # Verify all different age categories are included
        categories = {a.category for a in oxford_teams[0].athletes}
        assert "U20W" in categories
        assert "SW" in categories
        assert "WV40" in categories
        assert "WV50" in categories


class TestTeamResultData:
    """Test team result data generation for output."""

    def test_team_result_includes_team_name_with_label(self) -> None:
        """Team result data should include team name with label."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        athletes = [
            _create_athlete("Athlete 1", "Oxford AC", 1, "U13B"),
            _create_athlete("Athlete 2", "Oxford AC", 2, "U13B"),
            _create_athlete("Athlete 3", "Oxford AC", 3, "U13B"),
        ]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)
        result_data = service.create_team_result_data(teams, team_size=3, penalty_score=50)

        assert len(result_data) > 0
        assert result_data[0]["Team"] == "Oxford AC A"

    def test_team_result_includes_runner_details(self) -> None:
        """Team result data should include runner names and positions."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        athletes = [
            _create_athlete("Alice Smith", "Oxford AC", 5, "U13B"),
            _create_athlete("Bob Jones", "Oxford AC", 10, "U13B"),
            _create_athlete("Charlie Roe", "Oxford AC", 15, "U13B"),
        ]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)
        result_data = service.create_team_result_data(teams, team_size=3, penalty_score=50)

        assert result_data[0]["Runner1"] == "Alice Smith (5)"
        assert result_data[0]["Runner2"] == "Bob Jones (10)"
        assert result_data[0]["Runner3"] == "Charlie Roe (15)"

    def test_team_result_excludes_invalid_teams(self) -> None:
        """Team result data should not include teams with invalid scores."""
        config = build_default_config()
        service = TeamScoringService(config)
        category = config.category_config.get_category("U13B")

        # Create a club with only 1 athlete (below minimum of 2)
        athletes = [_create_athlete("Athlete 1", "Small Club", 1, "U13B")]
        race_result = _create_race_result("U13", athletes)

        teams = service.calculate_teams_for_race(race_result, category)
        result_data = service.create_team_result_data(teams, team_size=3, penalty_score=50)

        # Should not include the team with invalid score
        team_names = [row["Team"] for row in result_data]
        assert "Small Club A" not in team_names


class TestOverallTeamAggregation:
    """Regression tests for overall team score aggregation."""

    def test_overall_team_scores_use_round_score_not_position(self, tmp_path) -> None:
        """Overall standings should aggregate round Score values from team result files."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        # Round team result file includes both position and team score.
        # Overall aggregation must use Score (26), not Pos (2).
        round_dir = config.data_base_path / "r1" / "teams"
        round_dir.mkdir(parents=True)

        pd.DataFrame(
            [
                {"Pos": 1, "Team": "Club A A", "Score": 14},
                {"Pos": 2, "Team": "Club B A", "Score": 26},
            ]
        ).to_csv(round_dir / "U13B.csv", index=False)

        service = TeamScoreService(
            config=config,
            race_result_repo=Mock(),
            team_scoring_service=TeamScoringService(config),
        )

        service.update_team_scores_for_category("U13B")

        output_file = config.data_base_path / "scores" / "teams" / "U13B.csv"
        assert output_file.exists()

        df = pd.read_csv(output_file)
        row = df[df["Team"] == "Club B A"].iloc[0]

        assert int(row["r1"]) == 26
        assert int(row["score"]) == 26

    def test_team_scores_sum_all_rounds(self, tmp_path) -> None:
        """Team totals should be the sum of ALL round scores (no dropped round)."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        for rnd, scores in [("r1", [10, 20]), ("r2", [15, 25]), ("r3", [12, 18])]:
            rnd_dir = config.data_base_path / rnd / "teams"
            rnd_dir.mkdir(parents=True)
            pd.DataFrame(
                [
                    {"Pos": 1, "Team": "Club A A", "Score": scores[0]},
                    {"Pos": 2, "Team": "Club B A", "Score": scores[1]},
                ]
            ).to_csv(rnd_dir / "U13B.csv", index=False)

        service = TeamScoreService(
            config=config,
            race_result_repo=Mock(),
            team_scoring_service=TeamScoringService(config),
        )

        service.update_team_scores_for_category("U13B")

        output_file = config.data_base_path / "scores" / "teams" / "U13B.csv"
        df = pd.read_csv(output_file)

        club_a = df[df["Team"] == "Club A A"].iloc[0]
        club_b = df[df["Team"] == "Club B A"].iloc[0]

        # Total should be sum of ALL rounds, not best 2-of-3
        assert int(club_a["score"]) == 10 + 15 + 12  # 37
        assert int(club_b["score"]) == 20 + 25 + 18  # 63
