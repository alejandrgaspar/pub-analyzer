"""Works models."""

from enum import StrEnum

from pydantic import BaseModel, HttpUrl

from pub_analyzer.models.author import DehydratedAuthor


class WorkIDs(BaseModel):
    """IDs from a Work."""

    openalex: HttpUrl
    doi: HttpUrl | None = None
    mag: int | None = None
    pmid: str | None = None
    pmcid: str | None = None


class WorkDrivenVersion(StrEnum):
    """The version of the work, based on the Driver Guidelines versioning scheme."""

    submitted = "submittedVersion"
    accepted = "acceptedVersion"
    published = "publishedVersion"


class Location(BaseModel):
    """Describes the location of a given work."""

    is_oa: bool
    landing_page_url: HttpUrl
    license: str | None
    pdf_url: str | None
    version: WorkDrivenVersion | None


class OpenAccessStatus(StrEnum):
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


class Work(BaseModel):
    """Work Model Object from OpenAlex API definition."""

    id: HttpUrl
    ids: WorkIDs

    title: str
    publication_year: int
    publication_date: str
    language: str | None = None
    primary_location: Location
    type: str

    open_access: WorkAccessInfo
    authorships: list[Authorship]

    cited_by_count: int
    referenced_works_count: int

    referenced_works: list[HttpUrl]
    cited_by_api_url: HttpUrl
