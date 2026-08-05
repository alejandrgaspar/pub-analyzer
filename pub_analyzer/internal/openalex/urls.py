"""Builders for OpenAlex API URLs."""

import datetime
from collections.abc import Iterable
from typing import NewType

FromDate = NewType("FromDate", datetime.datetime)
"""DateTime marker for works published from this date."""

ToDate = NewType("ToDate", datetime.datetime)
"""DateTime marker for works published up to this date."""

BASE_URL = "https://api.openalex.org"
"""Root of the OpenAlex API."""

PER_PAGE_SIZE = 200
"""Results per page requested from the API, which is the maximum OpenAlex allows."""

AUTHOR_FILTER_KEY = "author.id"
"""Works filter selecting by author."""

INSTITUTION_FILTER_KEY = "institutions.id"
"""Works filter selecting by institution."""


def build_publication_date_filters(from_date: FromDate | None = None, to_date: ToDate | None = None) -> str:
    """Build the publication date fragment of a works filter.

    Args:
        from_date: Filter works published from this date.
        to_date: Filter works published up to this date.

    Returns:
        Filter fragment, ready to append to a filter list. Empty when no date is given.

    Example:
        ```python
        build_publication_date_filters(from_date, None)
        # ',from_publication_date:2020-01-01'
        ```
    """
    from_filter = f",from_publication_date:{from_date:%Y-%m-%d}" if from_date else ""
    to_filter = f",to_publication_date:{to_date:%Y-%m-%d}" if to_date else ""

    return from_filter + to_filter


def build_works_url(
    filter_key: str,
    entity_keys: Iterable[str],
    from_date: FromDate | None = None,
    to_date: ToDate | None = None,
) -> str:
    """Build the URL listing every work belonging to a set of entities.

    Args:
        filter_key: OpenAlex filter selecting the entity, e.g. `"author.id"`.
        entity_keys: OpenAlex keys of the entities whose works are listed.
        from_date: Filter works published from this date.
        to_date: Filter works published up to this date.

    Returns:
        Works URL with all filters and sorting applied.
    """
    entities_filter = "|".join(entity_keys)
    date_filters = build_publication_date_filters(from_date, to_date)

    return f"{BASE_URL}/works?filter={filter_key}:{entities_filter}{date_filters}&sort=publication_date&per-page={PER_PAGE_SIZE}"


def build_cited_by_url(work_key: str, from_date: FromDate | None = None, to_date: ToDate | None = None) -> str:
    """Build the URL listing every work citing a given work.

    Args:
        work_key: OpenAlex key of the cited work.
        from_date: Filter citing works published from this date.
        to_date: Filter citing works published up to this date.

    Returns:
        Works URL with all filters and sorting applied.
    """
    date_filters = build_publication_date_filters(from_date, to_date)

    return f"{BASE_URL}/works?filter=cites:{work_key}{date_filters}&sort=publication_date&per-page={PER_PAGE_SIZE}"


def build_source_url(source_key: str) -> str:
    """Build the URL of a single source.

    Args:
        source_key: OpenAlex key of the source.

    Returns:
        Source URL.
    """
    return f"{BASE_URL}/sources/{source_key}"
