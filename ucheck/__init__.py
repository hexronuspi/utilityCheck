"""
UtilityCheck Package

A utility package for various code analysis tasks including language detection.
"""

from .languagecheck.detector import languagecheck

__version__ = "1.0.0"
__author__ = "UtilityCheck Team"

__all__ = ["languagecheck"]