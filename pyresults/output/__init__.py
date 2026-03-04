"""Output generation layer.

This module provides abstractions for generating different output formats
(Excel, PDF, HTML) following the Interface Segregation Principle and Strategy
Pattern.

Score data preparation is centralised in ``ScoreDataProvider`` so that all
output generators render identical data.
"""

from .excel_output_generator import ExcelOutputGenerator
from .html_output_generator import HtmlOutputGenerator
from .interfaces import IOutputGenerator
from .pdf_output_generator import PdfOutputGenerator
from .round_results_excel_generator import RoundResultsExcelGenerator
from .score_data_provider import CategoryDisplayData, ScoreDataProvider

__all__ = [
    "CategoryDisplayData",
    "IOutputGenerator",
    "ExcelOutputGenerator",
    "HtmlOutputGenerator",
    "PdfOutputGenerator",
    "RoundResultsExcelGenerator",
    "ScoreDataProvider",
]
