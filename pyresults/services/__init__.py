"""Service layer containing business logic.

Services encapsulate business logic and orchestrate operations across
repositories and domain models. This layer follows the Single Responsibility
Principle by separating concerns into focused service classes.
"""

from .individual_score_service import IndividualScoreService
from .team_score_service import TeamScoreService
from .team_scoring_service import TeamScoringService

try:
    from .race_processor_service import RaceProcessorService
except ImportError:
    pass  # pandas not installed; RaceProcessorService unavailable

__all__ = [
    "RaceProcessorService",
    "IndividualScoreService",
    "TeamScoreService",
    "TeamScoringService",
]
