"""Institutions models."""

from pydantic import BaseModel


class DehydratedInstitution(BaseModel):
    """Stripped-down Institution Model."""

    id: str
    ror: str
    display_name: str
    country_code: str
    type: str
