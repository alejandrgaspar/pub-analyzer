"""Report Structure Objects."""

from enum import Enum

from pydantic import BaseModel

from pub_analyzer.models.author import Author
from pub_analyzer.models.work import Work


class CitationType(Enum):
    """Citation type Work."""

    TypeA = 0
    TypeB = 1


class CitationReport(BaseModel):
    """Cited by Works with stats."""

    work: Work
    citation_type: CitationType


class WorkReport(BaseModel):
    """Work model with stats."""

    work: Work
    cited_by: list[CitationReport]


class Report(BaseModel):
    """Citation Report Model."""

    author: Author
    works: list[WorkReport]

    #first_pub_date: date
