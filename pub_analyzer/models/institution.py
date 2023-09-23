"""Institutions models from OpenAlex API Schema definition."""

from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, Field, HttpUrl

InstitutionOpenAlexID: TypeAlias = HttpUrl
"""OpenAlex ID for Institution Objects with the format `https://openalex.org/I000000000`"""

InstitutionOpenAlexKey: TypeAlias = str
"""OpenAlex Institution entity Key with the format `I000000000`"""


class InstitutionIDs(BaseModel):
    """IDs from a Institution."""

    openalex: InstitutionOpenAlexID
    grid: str | None = None
    ror: HttpUrl | None = None
    wikipedia: HttpUrl | None = None
    wikidata: HttpUrl | None = None


class InstitutionType(str, Enum):
    """The institution's primary type, using the ROR "type" controlled vocabulary."""

    Education = "education"
    Healthcare = "healthcare"
    Company = "company"
    Archive = "archive"
    Nonprofit = "nonprofit"
    Government = "government"
    Facility = "facility"
    Other = "other"


class InstitutionSummaryStats(BaseModel):
    """Citation metrics for this Institution."""

    two_yr_mean_citedness: float = Field(..., alias="2yr_mean_citedness")
    h_index: int
    i10_index: int


class InstitutionYearCount(BaseModel):
    """Summary of published papers and number of citations in a year."""

    year: int
    works_count: int
    cited_by_count: int


class InstitutionGeo(BaseModel):
    """Location of the institution."""

    city: str
    geonames_city_id: str
    region: str | None = None
    country_code: str
    country: str


class InstitutionRoleType(str, Enum):
    """Possible institution roles."""

    funder = "funder"
    publisher = "publisher"
    institution = "institution"


class InstitutionRole(BaseModel):
    """Institution role."""

    role: InstitutionRoleType
    id: HttpUrl
    works_count: int


class Institution(BaseModel):
    """Universities and other organizations to which authors claim affiliations."""

    id: InstitutionOpenAlexID
    ids: InstitutionIDs

    display_name: str
    country_code: str
    type: InstitutionType
    homepage_url: HttpUrl | None = None

    works_count: int
    cited_by_count: int
    counts_by_year: list[InstitutionYearCount]
    summary_stats: InstitutionSummaryStats

    geo: InstitutionGeo
    roles: list[InstitutionRole]

    works_api_url: str


class DehydratedInstitution(BaseModel):
    """Stripped-down Institution Model."""

    id: InstitutionOpenAlexID
    ror: str
    display_name: str
    country_code: str
    type: InstitutionType


class InstitutionResult(BaseModel):
    """Institution result Model resulting from a search in OpenAlex."""

    id: InstitutionOpenAlexID
    display_name: str
    hint: str | None = None

    cited_by_count: int
    works_count: int

    entity_type: str
    external_id: str | None = None
