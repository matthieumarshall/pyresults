"""Output generation layer.

This module provides abstractions for generating different output formats
(Excel, PDF) following the Interface Segregation Principle and Strategy Pattern.

Score data preparation is centralised in ``ScoreDataProvider`` so that all
output generators render identical data.
"""

from .excel_output_generator import ExcelOutputGenerator
from .interfaces import IOutputGenerator
from .pdf_output_generator import PdfOutputGenerator
from .score_data_provider import CategoryDisplayData, ScoreDataProvider

__all__ = [
    "CategoryDisplayData",
    "IOutputGenerator",
    "ExcelOutputGenerator",
    "PdfOutputGenerator",
    "ScoreDataProvider",
]
