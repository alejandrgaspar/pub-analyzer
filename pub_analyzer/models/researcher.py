"""Researchers models."""

from pydantic import BaseModel, Field, validator


class ResearcherInfo(BaseModel):
    """Information DictType from a researcher resulting from a search in OpenAlex."""

    id: str
    display_name: str
    hint: str | None = ""
    cited_by_count: int
    works_count: int
    entity_type: str
    external_id: str | None = ""

    class Config:
        """Allowing a value to be assigned during validation."""

        validate_assignment = True

    @validator("hint", "external_id")
    def set_default(cls, value: str) -> str:
        """Define a default text."""
        return value or ""


class ExternalResearcherIDs(BaseModel):
    """IDs from a Researcher."""

    openalex: str
    orcid: str | None = ""
    mag: str | None = ""
    scopus: str | None = ""
    twitter: str | None = ""
    wikipedia: str | None = ""

    class Config:
        """Allowing a value to be assigned during validation."""

        validate_assignment = True

    @validator("mag", "scopus", "twitter", "wikipedia")
    def set_default(cls, value: str) -> str:
        """Define a default text."""
        return value or ""


class ResearcherInstitution(BaseModel):
    """Institution info from researcher."""

    id: str
    ror: str
    display_name: str
    country_code: str
    type: str


class ResearcherYearCount(BaseModel):
    """Summary of published papers and number of citations in a year."""

    year: int
    works_count: int
    cited_by_count: int


class ResearcherSummaryStats(BaseModel):
    """Citation metrics for this author."""

    two_yr_mean_citedness: float = Field(..., alias="2yr_mean_citedness")
    h_index: int
    i10_index: int


class ResearcherExtendedInfo(BaseModel):
    """Extended Information from a researcher get from OpenAlex."""

    id: str
    orcid: str | None = ""
    display_name: str
    display_name_alternatives: list[str]

    works_count: int
    cited_by_count: int

    ids: ExternalResearcherIDs
    last_known_institution: ResearcherInstitution | None
    counts_by_year: list[ResearcherYearCount]

    summary_stats: ResearcherSummaryStats

    works_api_url: str
