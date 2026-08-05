"""Functions to make reports."""

from pub_analyzer.internal.openalex.urls import FromDate, ToDate

from .builder import make_author_report, make_institution_report

__all__ = [
    "FromDate",
    "ToDate",
    "make_author_report",
    "make_institution_report",
]
