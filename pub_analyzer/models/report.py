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


class CitationResume(BaseModel):
    """Summary of citation information in all works."""

    type_a_count: int = 0
    type_b_count: int = 0

    def add_cite_type(self, cite_type: CitationType) -> None:
        """Add the type of cite in the corresponding counter."""
        if cite_type.value == CitationType.TypeA.value:
            self.type_a_count += 1
        elif cite_type.value == CitationType.TypeB.value:
            self.type_b_count += 1


class WorkReport(BaseModel):
    """Work model with stats."""

    work: Work
    cited_by: list[CitationReport]

    citation_resume: CitationResume

class Report(BaseModel):
    """Citation Report Model."""

    author: Author
    works: list[WorkReport]

    citation_resume: CitationResume
