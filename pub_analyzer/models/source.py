"""Sources models from OpenAlex API Schema definition."""

from pydantic import BaseModel, HttpUrl


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
       of their medium (print or electronic). [More info](https://www.issn.org/).
    """

    is_oa: bool
    """Whether this is currently fully-open-access source."""
    is_in_doaj: bool
    """Whether this is a journal listed in the [Directory of Open Access Journals](https://doaj.org) (DOAJ)."""

    host_organization: HttpUrl | None = None
    """The host organization for this source as an OpenAlex ID. This will be an
       [Institution.id][pub_analyzer.models.institution.Institution.id] if the source is a repository,
       and a Publisher.id if the source is a journal, conference, or eBook platform
    """
    host_organization_name: str | None = None
    """The display_name from the host_organization."""

    type: str
    """The type of source, which will be one of: `journal`, `repository`, `conference`,
       `ebook platform`, or `book series`.
    """
