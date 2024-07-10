"""Reports Structure Objects."""

from enum import Enum

from pydantic import BaseModel

from .author import Author
from .institution import Institution
from .source import Source
from .work import OpenAccessStatus, Work


class CitationType(Enum):
    """Citation type Work."""

    TypeA = 0
    TypeB = 1


class CitationReport(BaseModel):
    """Cited by Works with stats."""

    work: Work
    citation_type: CitationType


class CitationSummary(BaseModel):
    """Summary of citation information in all works."""

    type_a_count: int = 0
    type_b_count: int = 0

    def add_cite_type(self, cite_type: CitationType) -> None:
        """Add the type of cite in the corresponding counter."""
        if cite_type.value == CitationType.TypeA.value:
            self.type_a_count += 1
        elif cite_type.value == CitationType.TypeB.value:
            self.type_b_count += 1


class OpenAccessSummary(BaseModel):
    """Open Access Type counter."""

    diamond: int = 0
    gold: int = 0
    green: int = 0
    hybrid: int = 0
    bronze: int = 0
    closed: int = 0

    def add_oa_type(self, open_access_type: OpenAccessStatus) -> None:
        """Add the type of Open Access in the corresponding counter."""
        match open_access_type:
            case OpenAccessStatus.diamond:
                self.diamond += 1
            case OpenAccessStatus.gold:
                self.gold += 1
            case OpenAccessStatus.green:
                self.green += 1
            case OpenAccessStatus.hybrid:
                self.hybrid += 1
            case OpenAccessStatus.bronze:
                self.bronze += 1
            case OpenAccessStatus.closed:
                self.closed += 1


class WorkTypeCounter(BaseModel):
    """Work Type Counter."""

    type_name: str
    count: int


class WorkReport(BaseModel):
    """Work model with stats."""

    work: Work
    cited_by: list[CitationReport]

    citation_summary: CitationSummary


class SourcesSummary(BaseModel):
    """Sources model with stats."""

    sources: list[Source]


class AuthorReport(BaseModel):
    """Report of scientific production of an author."""

    author: Author
    works: list[WorkReport]

    citation_summary: CitationSummary
    open_access_summary: OpenAccessSummary
    works_type_summary: list[WorkTypeCounter]
    sources_summary: SourcesSummary


class InstitutionReport(BaseModel):
    """Scientific production report of the Institution."""

    institution: Institution
    works: list[WorkReport]

    citation_summary: CitationSummary
    open_access_summary: OpenAccessSummary
    works_type_summary: list[WorkTypeCounter]
    sources_summary: SourcesSummary
