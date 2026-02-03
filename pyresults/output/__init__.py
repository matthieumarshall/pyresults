"""Output generation layer.

This module provides abstractions for generating different output formats
(Excel, PDF) following the Interface Segregation Principle and Strategy Pattern.
"""

from .excel_output_generator import ExcelOutputGenerator
from .interfaces import IOutputGenerator
from .pdf_output_generator import PdfOutputGenerator

__all__ = [
    "IOutputGenerator",
    "ExcelOutputGenerator",
    "PdfOutputGenerator",
]
