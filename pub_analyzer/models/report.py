"""Report Structure Objects."""

from enum import IntEnum

from pydantic import BaseModel

from pub_analyzer.models.researcher import ResearcherExtendedInfo
from pub_analyzer.models.work import WorkInfo


class CitationType(IntEnum):
    """Citation type Work."""

    TypeA = 0
    TypeB = 1


class CitationReport(BaseModel):
    """Cited by Works with stats."""

    work: WorkInfo
    citation_type: CitationType


class WorkReport(BaseModel):
    """Work model with stats."""

    work: WorkInfo
    cited_by: list[CitationReport]


class Report(BaseModel):
    """Citation Report Model."""

    author: ResearcherExtendedInfo
    works: list[WorkReport]

    #first_pub_date: date
