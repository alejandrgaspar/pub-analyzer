"""Concept model from OpenAlex API Schema definition."""

from pydantic import BaseModel, HttpUrl


class DehydratedConcept(BaseModel):
    """Stripped-down Concept Model."""

    id: HttpUrl
    """The OpenAlex ID for this concept."""
    display_name: str
    """The English-language label of the concept."""

    wikidata: HttpUrl
    """The Wikidata ID for this concept. All OpenAlex concepts are also Wikidata concepts."""
    level: int
    """The level in the concept. Lower-level concepts are more general, and higher-level concepts are more specific."""
    score: float
    """The strength of the connection between the work and this concept (higher is stronger)."""
