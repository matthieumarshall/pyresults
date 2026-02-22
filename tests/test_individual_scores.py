from datetime import timedelta

from pyresults.config import build_default_config
from pyresults.domain import Athlete, DomainRaceResult
from pyresults.services import IndividualScoreService


class InMemoryRaceResultRepository:
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


class InMemoryScoreRepository:
    def __init__(self) -> None:
        self.saved_scores: dict[str, list] = {}

    def load_scores(self, category: str) -> list:
        return self.saved_scores.get(category, [])

    def save_scores(self, category: str, scores: list) -> None:
        self.saved_scores[category] = list(scores)

    def exists(self, category: str) -> bool:
        return category in self.saved_scores


def _build_race_result(
    round_number: str, placements: list[tuple[int, str, str]]
) -> DomainRaceResult:
    result = DomainRaceResult(race_name="U13", round_number=round_number)

    for position, name, club in placements:
        athlete = Athlete(
            name=name,
            club=club,
            race_number=str(100 + position),
            position=position,
            time=timedelta(minutes=10, seconds=position),
            gender="Male",
            category="U13B",
        )
        result.add_athlete(athlete)

    return result


def test_individual_score_service_counts_best_rounds() -> None:
    config = build_default_config()
    config.round_numbers = ["r1", "r2"]

    race_results = {
        ("U13", "r1"): _build_race_result(
            "r1",
            [
                (1, "Alice Smith", "Club A"),
                (2, "Bob Jones", "Club B"),
                (3, "Charlie Roe", "Club C"),
            ],
        ),
        ("U13", "r2"): _build_race_result(
            "r2",
            [
                (1, "Bob Jones", "Club B"),
                (2, "Alice Smith", "Club A"),
                (3, "Charlie Roe", "Club C"),
            ],
        ),
    }

    race_repo = InMemoryRaceResultRepository(race_results)
    score_repo = InMemoryScoreRepository()

    service = IndividualScoreService(
        config=config, race_result_repo=race_repo, score_repo=score_repo
    )
    service.update_scores_for_category("U13B")

    saved_scores = score_repo.saved_scores["U13B"]
    assert len(saved_scores) == 3

    # Test best 1 round scoring
    totals_best_1 = sorted(score.calculate_total_score(1) for score in saved_scores)
    assert totals_best_1 == [1, 1, 3]

    # Test total of all rounds (for standings)
    totals_all = sorted(score.calculate_total_score(2) for score in saved_scores)
    assert totals_all == [3, 3, 6]

    score_by_name = {score.name: score for score in saved_scores}
    assert score_by_name["Alice Smith"].round_scores == {"r1": 1, "r2": 2}
    assert score_by_name["Bob Jones"].round_scores == {"r1": 2, "r2": 1}
    assert score_by_name["Charlie Roe"].round_scores == {"r1": 3, "r2": 3}


# ---------- Overall scoring tests ----------


def _build_mens_race_result(
    round_number: str, placements: list[tuple[int, str, str, str]]
) -> DomainRaceResult:
    """Build a Men race result with mixed categories.

    Each placement is (position, name, club, category_code).
    """
    result = DomainRaceResult(race_name="Men", round_number=round_number)
    for position, name, club, category in placements:
        athlete = Athlete(
            name=name,
            club=club,
            race_number=str(200 + position),
            position=position,
            time=timedelta(minutes=30, seconds=position),
            gender="Male",
            category=category,
        )
        result.add_athlete(athlete)
    return result


def test_overall_score_uses_race_position_not_category_position() -> None:
    """Overall scoring should use the athlete's finishing position in the
    full race, not a position within their age category."""
    config = build_default_config()
    config.round_numbers = ["r1", "r2"]

    race_results = {
        ("Men", "r1"): _build_mens_race_result(
            "r1",
            [
                (1, "Fast Vet", "Club A", "MV40"),  # 1st overall, 1st MV40
                (2, "Fast Senior", "Club B", "SM"),  # 2nd overall, 1st SM
                (3, "Another Senior", "Club C", "SM"),  # 3rd overall, 2nd SM
                (4, "Slow Vet", "Club A", "MV40"),  # 4th overall, 2nd MV40
            ],
        ),
        ("Men", "r2"): _build_mens_race_result(
            "r2",
            [
                (1, "Fast Senior", "Club B", "SM"),  # 1st overall
                (2, "Fast Vet", "Club A", "MV40"),  # 2nd overall
                (3, "Slow Vet", "Club A", "MV40"),  # 3rd overall
                (4, "Another Senior", "Club C", "SM"),  # 4th overall
            ],
        ),
    }

    race_repo = InMemoryRaceResultRepository(race_results)
    score_repo = InMemoryScoreRepository()

    service = IndividualScoreService(
        config=config, race_result_repo=race_repo, score_repo=score_repo
    )
    service.update_scores_for_overall_category("MensOverall")

    saved = score_repo.saved_scores["MensOverall"]
    assert len(saved) == 4

    by_name = {s.name: s for s in saved}

    # Overall positions should be the race finishing positions
    assert by_name["Fast Vet"].round_scores == {"r1": 1, "r2": 2}
    assert by_name["Fast Senior"].round_scores == {"r1": 2, "r2": 1}
    assert by_name["Another Senior"].round_scores == {"r1": 3, "r2": 4}
    assert by_name["Slow Vet"].round_scores == {"r1": 4, "r2": 3}

    # Best 1 of 2 rounds
    assert by_name["Fast Vet"].calculate_total_score(1) == 1
    assert by_name["Fast Senior"].calculate_total_score(1) == 1
    assert by_name["Slow Vet"].calculate_total_score(1) == 3
    assert by_name["Another Senior"].calculate_total_score(1) == 3


def test_overall_scores_included_in_update_all_categories() -> None:
    """update_all_categories should also compute overall standings."""
    config = build_default_config()
    config.round_numbers = ["r1"]

    race_results = {
        ("Men", "r1"): _build_mens_race_result(
            "r1",
            [
                (1, "Runner A", "Club A", "SM"),
                (2, "Runner B", "Club B", "MV40"),
            ],
        ),
    }

    race_repo = InMemoryRaceResultRepository(race_results)
    score_repo = InMemoryScoreRepository()

    service = IndividualScoreService(
        config=config, race_result_repo=race_repo, score_repo=score_repo
    )
    service.update_all_categories()

    # MensOverall should now be populated
    assert "MensOverall" in score_repo.saved_scores
    overall = score_repo.saved_scores["MensOverall"]
    assert len(overall) == 2

    by_name = {s.name: s for s in overall}
    assert by_name["Runner A"].round_scores == {"r1": 1}
    assert by_name["Runner B"].round_scores == {"r1": 2}
