"""Authors models from OpenAlex API Schema definition."""

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from pub_analyzer.models.institution import DehydratedInstitution

AuthorOpenAlexID: TypeAlias = HttpUrl
"""OpenAlex ID for Author Objects with the format `https://openalex.org/A000000000`"""

AuthorOpenAlexKey: TypeAlias = str
"""OpenAlex author entity Key with the format `A000000000`"""

class AuthorIDs(BaseModel):
    """IDs from an Author."""

    openalex: str
    orcid: str | None = ""
    scopus: str | None = ""
    twitter: str | None = ""
    wikipedia: str | None = ""

    # Allowing a value to be assigned during validation.
    model_config = ConfigDict(validate_assignment=True)

    @field_validator("scopus", "twitter", "wikipedia")
    def set_default(cls, value: str) -> str:
        """Define a default text."""
        return value or ""


class AuthorYearCount(BaseModel):
    """Summary of published papers and number of citations in a year."""

    year: int
    works_count: int
    cited_by_count: int


class AuthorSummaryStats(BaseModel):
    """Citation metrics for this author."""

    two_yr_mean_citedness: float = Field(..., alias="2yr_mean_citedness")
    h_index: int
    i10_index: int


class Author(BaseModel):
    """Author Model Object from OpenAlex API definition."""

    id: AuthorOpenAlexID
    ids: AuthorIDs
    orcid: str | None = ""

    display_name: str
    display_name_alternatives: list[str]

    works_count: int
    cited_by_count: int

    last_known_institution: DehydratedInstitution | None
    counts_by_year: list[AuthorYearCount]

    summary_stats: AuthorSummaryStats

    works_api_url: str


class DehydratedAuthor(BaseModel):
    """Stripped-down Author Model."""

    id: AuthorOpenAlexID
    display_name: str | None = None
    orcid: HttpUrl | None = None


class AuthorResult(BaseModel):
    """Author result Model resulting from a search in OpenAlex."""

    id: AuthorOpenAlexID
    display_name: str
    hint: str | None = ""
    cited_by_count: int
    works_count: int
    entity_type: str
    external_id: str | None = ""

    # Allowing a value to be assigned during validation.
    model_config = ConfigDict(validate_assignment=True)

    @field_validator("hint", "external_id")
    def set_default(cls, value: str) -> str:
        """Define a default text."""
        return value or ""
