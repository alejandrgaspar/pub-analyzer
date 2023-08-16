"""Sources models from OpenAlex API Schema definition."""

from pydantic import BaseModel, HttpUrl


class DehydratedSource(BaseModel):
    """Stripped-down Source Model."""

    id: HttpUrl
    display_name: str

    issn_l: str | None = None
    issn: list[str] | None = None

    is_oa: bool | None = False
    is_in_doaj: bool | None = False

    host_organization: HttpUrl | None = None
    host_organization_name: str | None = None

    type: str
