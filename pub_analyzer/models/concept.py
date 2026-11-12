"""Concept model from OpenAlex API Schema definition."""

from pydantic import BaseModel


class DehydratedConcept(BaseModel):
    """Stripped-down Concept Model."""

    id: str
    """The OpenAlex ID for this concept."""
    display_name: str
    """The English-language label of the concept."""

    wikidata: str
    """The Wikidata ID for this concept. All OpenAlex concepts are also Wikidata concepts."""
    level: int
    """The level in the concept. Lower-level concepts are more general, and higher-level concepts are more specific."""
    score: float
    """The strength of the connection between the work and this concept (higher is stronger)."""
