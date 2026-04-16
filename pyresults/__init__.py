"""pyresults – Running standings calculations.

Public API for use as a library.  Import the classes you need directly:

    from pyresults import (
        CompetitionConfig,
        build_default_config,
        IndividualScoreService,
        TeamScoringService,
        TeamScoreService,
        InMemoryRaceResultRepository,
        InMemoryScoreRepository,
        InMemoryTeamResultRepository,
        DomainRaceResult,
        Athlete,
    )

CSV implementations and output generators require the ``[output]`` extra
(pandas, openpyxl, fpdf, numpy).
"""

from pyresults.config import (
    CategoryConfig,
    CompetitionConfig,
    build_default_categories,
    build_default_config,
)
from pyresults.domain import (
    Athlete,
    Category,
    CategoryType,
    DomainRaceResult,
    DomainRound,
    Gender,
    Score,
    Team,
)
from pyresults.repositories import (
    IRaceResultRepository,
    IScoreRepository,
    ITeamResultRepository,
    InMemoryRaceResultRepository,
    InMemoryScoreRepository,
    InMemoryTeamResultRepository,
)
from pyresults.services import (
    IndividualScoreService,
    TeamScoreService,
    TeamScoringService,
)


def get_valid_category_codes() -> frozenset[str]:
    """Return the set of all valid category codes for this competition.

    Useful for validating that raw category strings (e.g. from CSV imports)
    match the codes expected by the scoring services.

    Example::

        from pyresults import get_valid_category_codes
        assert "MV40" in get_valid_category_codes()
    """
    return frozenset(c.code for c in build_default_categories().get_all_categories())


__all__ = [
    # Config
    "CompetitionConfig",
    "CategoryConfig",
    "build_default_config",
    "build_default_categories",
    "get_valid_category_codes",
    # Domain
    "Athlete",
    "Team",
    "Score",
    "Category",
    "CategoryType",
    "Gender",
    "DomainRaceResult",
    "DomainRound",
    # Services
    "IndividualScoreService",
    "TeamScoringService",
    "TeamScoreService",
    # Repository interfaces
    "IRaceResultRepository",
    "IScoreRepository",
    "ITeamResultRepository",
    # In-memory implementations
    "InMemoryRaceResultRepository",
    "InMemoryScoreRepository",
    "InMemoryTeamResultRepository",
]
