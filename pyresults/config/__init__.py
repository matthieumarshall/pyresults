"""Configuration module providing competition configuration.

This module replaces the hard-coded CONFIG.py constants with a proper
configuration class that can be injected, following Dependency Inversion
Principle and Open/Closed Principle.
"""

from .category_config import CategoryConfig, build_default_categories
from .competition_config import CompetitionConfig, build_default_config

__all__ = [
    "CompetitionConfig",
    "CategoryConfig",
    "build_default_categories",
    "build_default_config",
]
