"""Repository interfaces and implementations for data access.

This layer provides abstractions over data storage, following the Repository
pattern and Dependency Inversion Principle. Business logic depends on these
abstractions, not on concrete implementations.

CSV implementations (CsvRaceResultRepository, CsvScoreRepository,
CsvTeamResultRepository) require the ``[output]`` optional dependency group
(pandas).  In-memory implementations and interfaces are always available.
"""

from .in_memory_repositories import (
    InMemoryRaceResultRepository,
    InMemoryScoreRepository,
    InMemoryTeamResultRepository,
)
from .interfaces import (
    IRaceResultRepository,
    IScoreRepository,
    ITeamResultRepository,
)

__all__ = [
    "IRaceResultRepository",
    "IScoreRepository",
    "ITeamResultRepository",
    "InMemoryRaceResultRepository",
    "InMemoryScoreRepository",
    "InMemoryTeamResultRepository",
]

# CSV implementations are optional (require pandas via pyresults[output]).
try:
    from .csv_race_result_repository import CsvRaceResultRepository
    from .csv_score_repository import CsvScoreRepository
    from .csv_team_result_repository import CsvTeamResultRepository

    __all__ += [
        "CsvRaceResultRepository",
        "CsvScoreRepository",
        "CsvTeamResultRepository",
    ]
except ImportError:
    pass
