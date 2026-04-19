"""In-memory repository implementations for testing and library usage.

These implementations hold data entirely in Python dicts/lists so that the
scoring services can be used without any filesystem access.  They are the
primary integration point for external consumers such as the website backend,
which builds domain objects from a database query and passes them through
the scoring services without ever touching the filesystem.
"""

from pyresults.domain import DomainRaceResult, Score

from .interfaces import IRaceResultRepository, IScoreRepository, ITeamResultRepository


class InMemoryRaceResultRepository(IRaceResultRepository):
    """Race result repository backed by an in-memory dict.

    Keys are ``(race_name, round_number)`` tuples.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], DomainRaceResult] = {}

    def load_race_result(self, race_name: str, round_number: str) -> DomainRaceResult | None:
        return self._store.get((race_name, round_number))

    def save_race_result(self, race_result: DomainRaceResult) -> None:
        self._store[(race_result.race_name, race_result.round_number)] = race_result

    def exists(self, race_name: str, round_number: str) -> bool:
        return (race_name, round_number) in self._store

    def get_available_races(self, round_number: str) -> list[str]:
        return [race_name for (race_name, rn) in self._store if rn == round_number]

    # ------------------------------------------------------------------
    # Convenience helpers (not part of interface)
    # ------------------------------------------------------------------

    def populate(self, race_results: list[DomainRaceResult]) -> None:
        """Bulk-load a list of race results into the store."""
        for rr in race_results:
            self.save_race_result(rr)


class InMemoryScoreRepository(IScoreRepository):
    """Score repository backed by an in-memory dict.

    Keys are category code strings.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[Score]] = {}

    def load_scores(self, category: str) -> list[Score]:
        return list(self._store.get(category, []))

    def save_scores(self, category: str, scores: list[Score]) -> None:
        self._store[category] = list(scores)

    def exists(self, category: str) -> bool:
        return category in self._store and bool(self._store[category])

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def all_scores(self) -> dict[str, list[Score]]:
        """Return a copy of the entire score store."""
        return dict(self._store)


class InMemoryTeamResultRepository(ITeamResultRepository):
    """Team result repository backed by an in-memory dict.

    Keys are ``(category_code, round_number)`` tuples.  Each value is a list
    of row dicts with at minimum ``"team"`` and ``"pos"`` keys.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[dict]] = {}

    def load_team_results(self, category_code: str, round_number: str) -> list[dict]:
        return list(self._store.get((category_code, round_number), []))

    def save_team_results(self, category_code: str, round_number: str, data: list[dict]) -> None:
        # Normalise keys to lower-case so that TeamScoreService can read them
        # with lowercase lookups (.get("team"), .get("pos"), .get("score")),
        # matching the behaviour of CsvTeamResultRepository which applies
        # df.columns.str.lower() on load.
        normalized = [{k.lower(): v for k, v in row.items()} for row in data]
        self._store[(category_code, round_number)] = normalized

    def team_results_exist(self, category_code: str, round_number: str) -> bool:
        return bool(self._store.get((category_code, round_number)))
