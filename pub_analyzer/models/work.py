"""Works models from OpenAlex API Schema definition."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, HttpUrl, field_validator

from .author import DehydratedAuthor
from .source import DehydratedSource


class WorkIDs(BaseModel):
    """IDs from a Work."""

    openalex: HttpUrl
    doi: HttpUrl | None = None
    pmid: str | None = None
    pmcid: str | None = None


class WorkDrivenVersion(str, Enum):
    """The version of the work, based on the Driver Guidelines versioning scheme."""

    submitted = "submittedVersion"
    accepted = "acceptedVersion"
    published = "publishedVersion"


class Location(BaseModel):
    """Describes the location of a given work."""

    is_oa: bool
    landing_page_url: str
    license: str | None
    pdf_url: str | None
    version: WorkDrivenVersion | None
    source: DehydratedSource  | None = None


class OpenAccessStatus(str, Enum):
    """The Open Access (OA) status of this work."""

    gold = "gold"
    green = "green"
    hybrid = "hybrid"
    bronze = "bronze"
    closed = "closed"


class WorkAccessInfo(BaseModel):
    """Information about the access status of this work."""

    is_oa: bool
    oa_status: OpenAccessStatus
    oa_url: HttpUrl | None = None
    any_repository_has_fulltext: bool


class Authorship(BaseModel):
    """Information of author and her institutional affiliations in the context of work."""

    author_position: str
    author: DehydratedAuthor


class ArticleProcessingCharge(BaseModel):
    """Information about the paid APC for this work."""

    value: int
    currency: str
    provenance: str
    value_usd: int | None


class Work(BaseModel):
    """Work Model Object from OpenAlex API definition."""

    id: HttpUrl
    ids: WorkIDs

    title: str
    abstract: str | None = None
    publication_year: int
    publication_date: str
    language: str | None = None
    type: str

    primary_location: Location | None = None
    best_oa_location: Location | None = None
    locations: list[Location]

    open_access: WorkAccessInfo
    authorships: list[Authorship]

    cited_by_count: int

    referenced_works: list[HttpUrl]
    cited_by_api_url: HttpUrl

    apc_list: ArticleProcessingCharge | None = None
    """The price as listed by the journal's publisher."""
    apc_paid: ArticleProcessingCharge | None = None
    """APC actually paid by authors."""

    @field_validator('locations', mode='before')
    def valid_locations(cls, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Skip locations that do not contain enough data."""
        return [location for location in locations if location['landing_page_url'] is not None]

    @field_validator('primary_location', 'best_oa_location', mode='before')
    def valid_location(cls, location: dict[str, Any]) -> dict[str, Any] | None:
        """Skip location that do not contain enough data."""
        if location and location['landing_page_url'] is None:
            return None
        else:
            return location

    @field_validator('authorships', mode='before')
    def valid_authorships(cls, authorships: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Skip authorships that do not contain enough data."""
        return [authorship for authorship in authorships if authorship['author'].get("id") is not None]
