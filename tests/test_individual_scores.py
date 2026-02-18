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


def _build_race_result(round_number: str, placements: list[tuple[int, str, str]]) -> DomainRaceResult:
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
            "r1", [(1, "Alice Smith", "Club A"), (2, "Bob Jones", "Club B"), (3, "Charlie Roe", "Club C")]
        ),
        ("U13", "r2"): _build_race_result(
            "r2", [(1, "Bob Jones", "Club B"), (2, "Alice Smith", "Club A"), (3, "Charlie Roe", "Club C")]
        ),
    }

    race_repo = InMemoryRaceResultRepository(race_results)
    score_repo = InMemoryScoreRepository()

    service = IndividualScoreService(config=config, race_result_repo=race_repo, score_repo=score_repo)
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
