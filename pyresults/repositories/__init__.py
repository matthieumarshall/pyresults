"""Repository interfaces and implementations for data access.

This layer provides abstractions over data storage, following the Repository
pattern and Dependency Inversion Principle. Business logic depends on these
abstractions, not on concrete implementations.
"""

from .csv_race_result_repository import CsvRaceResultRepository
from .csv_score_repository import CsvScoreRepository
from .interfaces import (
    IRaceResultRepository,
    IScoreRepository,
)

__all__ = [
    "IRaceResultRepository",
    "IScoreRepository",
    "CsvRaceResultRepository",
    "CsvScoreRepository",
]
