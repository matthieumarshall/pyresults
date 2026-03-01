"""Tests for partial/incomplete round data.

Validates that the system handles gracefully when only some race files
exist for a given round (e.g. round 5 only has Men.csv but not Women.csv).
"""

import types
from datetime import timedelta

import pandas as pd

from pyresults.config import build_default_config
from pyresults.domain import Athlete, DomainRaceResult
from pyresults.repositories import IRaceResultRepository, IScoreRepository
from pyresults.results_processor import ResultsProcessor
from pyresults.services import IndividualScoreService

# ---------------------------------------------------------------------------
# In-memory test doubles (shared with other test modules)
# ---------------------------------------------------------------------------


class InMemoryRaceResultRepository(IRaceResultRepository):
    def __init__(self, results: dict[tuple[str, str], DomainRaceResult]) -> None:
        self._results = results

    def load_race_result(self, race_name: str, round_number: str) -> DomainRaceResult | None:
        return self._results.get((race_name, round_number))

    def save_race_result(self, race_result: DomainRaceResult) -> None:
        pass

    def exists(self, race_name: str, round_number: str) -> bool:
        return (race_name, round_number) in self._results

    def get_available_races(self, round_number: str) -> list[str]:
        return [race for race, rnd in self._results.keys() if rnd == round_number]


class InMemoryScoreRepository(IScoreRepository):
    def __init__(self) -> None:
        self.saved_scores: dict[str, list] = {}

    def load_scores(self, category: str) -> list:
        return self.saved_scores.get(category, [])

    def save_scores(self, category: str, scores: list) -> None:
        self.saved_scores[category] = list(scores)

    def exists(self, category: str) -> bool:
        return category in self.saved_scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_INPUT_MEN = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,201,John Smith,00:30:01,Senior Men,1,Male,1,Club A
2,202,Dave Jones,00:31:15,V40,1,Male,2,Club B
3,203,Tom Brown,00:32:00,Senior Men,2,Male,3,Club C
"""

_SAMPLE_INPUT_U13 = """\
Pos,Race No,Name,Time,Category,Cat Pos,Gender,Gen Pos,Club
1,301,Alice Wonder,00:08:10,U13 Boys,1,Male,1,Club A
2,302,Bob Builder,00:08:30,U13 Girls,1,Female,1,Club B
"""


def _build_race_result(
    race_name: str,
    round_number: str,
    placements: list[tuple[int, str, str, str]],
) -> DomainRaceResult:
    """Build a race result with (position, name, club, category)."""
    result = DomainRaceResult(race_name=race_name, round_number=round_number)
    for position, name, club, category in placements:
        athlete = Athlete(
            name=name,
            club=club,
            race_number=str(100 + position),
            position=position,
            time=timedelta(minutes=10, seconds=position),
            gender="Male",
            category=category,
        )
        result.add_athlete(athlete)
    return result


# ---------------------------------------------------------------------------
# Test: partial round 5 via the ResultsProcessor (integration / end-to-end)
# ---------------------------------------------------------------------------


class TestPartialRoundProcessing:
    """Process a round where only some CSV files are present."""

    def test_only_one_race_file_in_round(self, tmp_path, monkeypatch) -> None:
        """When r5 only contains Men.csv, the processor should succeed and
        produce output for Men but not for missing races."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        processor = ResultsProcessor(config=config)
        # Stub out team scoring to isolate race processing
        processor._process_team_scores_for_race = types.MethodType(  # type: ignore[assignment]
            lambda self, race_result: None, processor
        )

        input_dir = tmp_path / "input_data" / "r5"
        input_dir.mkdir(parents=True)

        # Only write Men.csv — no Women, U11, U13, etc.
        (input_dir / "Men.csv").write_text(_SAMPLE_INPUT_MEN, encoding="utf-16")

        monkeypatch.chdir(tmp_path)
        processor._process_round("r5")

        # Men output should exist
        men_output = config.data_base_path / "r5" / "Men.csv"
        assert men_output.exists()
        df = pd.read_csv(men_output)
        assert len(df) == 3

        # Women and youth outputs should NOT exist
        assert not (config.data_base_path / "r5" / "Women.csv").exists()
        assert not (config.data_base_path / "r5" / "U13.csv").exists()

    def test_two_race_files_in_round(self, tmp_path, monkeypatch) -> None:
        """Partial round with two race files succeeds for both."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        processor = ResultsProcessor(config=config)
        processor._process_team_scores_for_race = types.MethodType(  # type: ignore[assignment]
            lambda self, race_result: None, processor
        )

        input_dir = tmp_path / "input_data" / "r5"
        input_dir.mkdir(parents=True)

        (input_dir / "Men.csv").write_text(_SAMPLE_INPUT_MEN, encoding="utf-16")
        (input_dir / "U13.csv").write_text(_SAMPLE_INPUT_U13, encoding="utf-16")

        monkeypatch.chdir(tmp_path)
        processor._process_round("r5")

        assert (config.data_base_path / "r5" / "Men.csv").exists()
        assert (config.data_base_path / "r5" / "U13.csv").exists()
        assert not (config.data_base_path / "r5" / "Women.csv").exists()

    def test_empty_round_directory(self, tmp_path, monkeypatch) -> None:
        """An empty input directory (no CSV files) should succeed silently."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        processor = ResultsProcessor(config=config)

        input_dir = tmp_path / "input_data" / "r5"
        input_dir.mkdir(parents=True)

        monkeypatch.chdir(tmp_path)
        # Should not raise
        processor._process_round("r5")

        # No output directory created
        assert not (config.data_base_path / "r5").exists()

    def test_missing_round_directory(self, tmp_path, monkeypatch) -> None:
        """When the input directory for a round doesn't exist at all,
        the processor should skip it gracefully."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"

        processor = ResultsProcessor(config=config)

        monkeypatch.chdir(tmp_path)
        # r5 directory doesn't exist at all
        processor._process_round("r5")

        assert not (config.data_base_path / "r5").exists()


# ---------------------------------------------------------------------------
# Test: individual scoring with a partial extra round
# ---------------------------------------------------------------------------


class TestScoringWithPartialRound:
    """When an extra round has data for some races but not others,
    scoring should still work and athletes from the partial round
    should be integrated correctly."""

    def test_individual_scores_with_partial_extra_round(self) -> None:
        """Athletes who appear in round 3 (partial) should have their
        scores updated; athletes who didn't race in round 3 still have
        correct totals from rounds 1 and 2."""
        config = build_default_config()
        config.round_numbers = ["r1", "r2", "r3"]

        race_results = {
            ("U13", "r1"): _build_race_result(
                "U13",
                "r1",
                [
                    (1, "Alice Smith", "Club A", "U13B"),
                    (2, "Bob Jones", "Club B", "U13B"),
                    (3, "Charlie Roe", "Club C", "U13B"),
                ],
            ),
            ("U13", "r2"): _build_race_result(
                "U13",
                "r2",
                [
                    (1, "Bob Jones", "Club B", "U13B"),
                    (2, "Alice Smith", "Club A", "U13B"),
                    (3, "Charlie Roe", "Club C", "U13B"),
                ],
            ),
            # r3 partial — only Alice and a newcomer raced
            ("U13", "r3"): _build_race_result(
                "U13",
                "r3",
                [
                    (1, "Alice Smith", "Club A", "U13B"),
                    (2, "New Runner", "Club D", "U13B"),
                ],
            ),
        }

        race_repo = InMemoryRaceResultRepository(race_results)
        score_repo = InMemoryScoreRepository()

        service = IndividualScoreService(
            config=config, race_result_repo=race_repo, score_repo=score_repo
        )
        service.update_scores_for_category("U13B")

        saved = score_repo.saved_scores["U13B"]
        by_name = {s.name: s for s in saved}

        # Alice ran all 3 rounds
        assert by_name["Alice Smith"].round_scores == {"r1": 1, "r2": 2, "r3": 1}
        # Bob ran 2 rounds
        assert by_name["Bob Jones"].round_scores == {"r1": 2, "r2": 1}
        # Charlie ran 2 rounds
        assert by_name["Charlie Roe"].round_scores == {"r1": 3, "r2": 3}
        # Newcomer only ran 1 round
        assert by_name["New Runner"].round_scores == {"r3": 2}

        # Best-2-of-3 scoring
        assert by_name["Alice Smith"].calculate_total_score(2) == 2  # 1+1
        assert by_name["Bob Jones"].calculate_total_score(2) == 3  # 1+2
        assert by_name["Charlie Roe"].calculate_total_score(2) == 6  # 3+3
        assert by_name["New Runner"].calculate_total_score(2) == 999999  # only 1 round

    def test_overall_scores_with_race_missing_from_later_round(self) -> None:
        """When the Men's race doesn't have data for a round, overall
        scoring should still work from the rounds that do exist."""
        config = build_default_config()
        config.round_numbers = ["r1", "r2", "r3"]

        race_results = {
            ("Men", "r1"): _build_race_result(
                "Men",
                "r1",
                [
                    (1, "Runner A", "Club A", "SM"),
                    (2, "Runner B", "Club B", "MV40"),
                ],
            ),
            ("Men", "r2"): _build_race_result(
                "Men",
                "r2",
                [
                    (1, "Runner B", "Club B", "MV40"),
                    (2, "Runner A", "Club A", "SM"),
                ],
            ),
            # r3 has NO Men race data — only U13 exists (simulated by absence)
        }

        race_repo = InMemoryRaceResultRepository(race_results)
        score_repo = InMemoryScoreRepository()

        service = IndividualScoreService(
            config=config, race_result_repo=race_repo, score_repo=score_repo
        )
        service.update_scores_for_overall_category("MensOverall")

        saved = score_repo.saved_scores["MensOverall"]
        assert len(saved) == 2

        by_name = {s.name: s for s in saved}
        # Only 2 rounds processed; best-1-of-2
        assert by_name["Runner A"].calculate_total_score(1) == 1
        assert by_name["Runner B"].calculate_total_score(1) == 1

    def test_no_rounds_with_data_produces_empty_scores(self) -> None:
        """If a category has zero data across all rounds, produce an empty
        score list without errors."""
        config = build_default_config()
        config.round_numbers = ["r1", "r2"]

        # No race results at all
        race_repo = InMemoryRaceResultRepository({})
        score_repo = InMemoryScoreRepository()

        service = IndividualScoreService(
            config=config, race_result_repo=race_repo, score_repo=score_repo
        )
        service.update_scores_for_category("U13B")

        saved = score_repo.saved_scores["U13B"]
        assert saved == []


# ---------------------------------------------------------------------------
# Test: full pipeline with partial final round
# ---------------------------------------------------------------------------


class TestFullPipelinePartialRound:
    """End-to-end: process multiple rounds including a partial final round,
    then aggregate individual scores."""

    def test_process_rounds_with_partial_final_round(self, tmp_path, monkeypatch) -> None:
        """process_rounds with r1 (full) and r2 (partial - only U13)
        should not raise and should produce scores for categories that
        have data."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        config.round_numbers = ["r1", "r2"]

        processor = ResultsProcessor(config=config)
        # Stub out team scoring and output generation
        processor._process_team_scores_for_race = types.MethodType(  # type: ignore[assignment]
            lambda self, race_result: None, processor
        )

        # Create r1 with Men and U13
        r1_dir = tmp_path / "input_data" / "r1"
        r1_dir.mkdir(parents=True)
        (r1_dir / "Men.csv").write_text(_SAMPLE_INPUT_MEN, encoding="utf-16")
        (r1_dir / "U13.csv").write_text(_SAMPLE_INPUT_U13, encoding="utf-16")

        # Create r2 with ONLY U13 (partial round)
        r2_dir = tmp_path / "input_data" / "r2"
        r2_dir.mkdir(parents=True)
        (r2_dir / "U13.csv").write_text(_SAMPLE_INPUT_U13, encoding="utf-16")

        monkeypatch.chdir(tmp_path)

        # Should not raise
        processor.process_rounds(["r1", "r2"], create_excel=False, create_pdf=False)

        # Individual scores should exist for categories that had data
        u13b_scores = config.data_base_path / "scores" / "U13B.csv"
        assert u13b_scores.exists()

        # SM scores should exist (from r1 Men race)
        sm_scores = config.data_base_path / "scores" / "SM.csv"
        assert sm_scores.exists()

    def test_process_rounds_skips_nonexistent_round(self, tmp_path, monkeypatch) -> None:
        """process_rounds handles a list containing a round with no input
        directory at all."""
        config = build_default_config()
        config.data_base_path = tmp_path / "data"
        config.round_numbers = ["r1", "r2"]

        processor = ResultsProcessor(config=config)
        processor._process_team_scores_for_race = types.MethodType(  # type: ignore[assignment]
            lambda self, race_result: None, processor
        )

        r1_dir = tmp_path / "input_data" / "r1"
        r1_dir.mkdir(parents=True)
        (r1_dir / "U13.csv").write_text(_SAMPLE_INPUT_U13, encoding="utf-16")

        # r2 directory does NOT exist

        monkeypatch.chdir(tmp_path)
        # Should not raise
        processor.process_rounds(["r1", "r2"], create_excel=False, create_pdf=False)

        # U13B scores should still be generated from r1
        u13b_scores = config.data_base_path / "scores" / "U13B.csv"
        assert u13b_scores.exists()
