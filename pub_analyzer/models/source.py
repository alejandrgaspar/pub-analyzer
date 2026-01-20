"""Sources models from OpenAlex API Schema definition."""

from pydantic import BaseModel, Field, HttpUrl


class SourceSummaryStats(BaseModel):
    """Citation metrics for this Source."""

    two_yr_mean_citedness: float = Field(..., alias="2yr_mean_citedness")
    """The 2-year mean citedness for this source. Also known as impact factor."""
    h_index: int
    """The h-index for this source."""
    i10_index: int
    """The i-10 index for this source."""


class SourceYearCount(BaseModel):
    """Summary of published papers and number of citations in a year."""

    year: int
    """Year."""
    works_count: int
    """The number of Works this source hosts in this year."""
    cited_by_count: int
    """The total number of Works that cite a Work hosted in this source in this year."""


class DehydratedSource(BaseModel):
    """Stripped-down Source Model."""

    id: HttpUrl
    """The OpenAlex ID for this source."""
    display_name: str
    """The name of the source."""

    issn_l: str | None = None
    """The ISSN-L identifying this source. The ISSN-L designating a single canonical ISSN
       for all media versions of the title. It's usually the same as the print ISSN.
    """
    issn: list[str] | None = None
    """The ISSNs used by this source. An ISSN identifies all continuing resources, irrespective
       of their medium (print or electronic). [More info](https://www.issn.org/){target=_blank}.
    """

    is_oa: bool
    """Whether this is currently fully-open-access source."""
    is_in_doaj: bool
    """Whether this is a journal listed in the [Directory of Open Access Journals](https://doaj.org){target=_blank} (DOAJ)."""

    host_organization: HttpUrl | None = None
    """The host organization for this source as an OpenAlex ID. This will be an
       [Institution.id][pub_analyzer.models.institution.Institution.id] if the source is a repository,
       and a Publisher.id if the source is a journal, conference, or eBook platform
    """
    host_organization_name: str | None = None
    """The display_name from the host_organization."""

    type: str | None = None
    """The type of source, which will be one of: `journal`, `repository`, `conference`,
       `ebook platform`, or `book series`.
    """


class Source(DehydratedSource):
    """Where works are hosted."""

    homepage_url: HttpUrl | None = None
    """The homepage for this source's website."""

    is_in_doaj: bool
    """Whether this is a journal listed in the Directory of Open Access Journals (DOAJ)."""

    summary_stats: SourceSummaryStats
    """Citation metrics for this source."""

    counts_by_year: list[SourceYearCount]
    """works_count and cited_by_count for each of the last ten years, binned by year."""
