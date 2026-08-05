"""Test URL builders from pub_analyzer/internal/openalex/urls.py."""

import datetime

import pytest

from pub_analyzer.internal.openalex import urls

FROM_DATE = urls.FromDate(datetime.datetime(2020, 1, 2))
TO_DATE = urls.ToDate(datetime.datetime(2023, 11, 30))


@pytest.mark.parametrize(
    ["from_date", "to_date", "expected"],
    [
        pytest.param(None, None, "", id="no-dates"),
        pytest.param(FROM_DATE, None, ",from_publication_date:2020-01-02", id="from-only"),
        pytest.param(None, TO_DATE, ",to_publication_date:2023-11-30", id="to-only"),
        pytest.param(
            FROM_DATE,
            TO_DATE,
            ",from_publication_date:2020-01-02,to_publication_date:2023-11-30",
            id="both",
        ),
    ],
)
def test_build_publication_date_filters(from_date: urls.FromDate | None, to_date: urls.ToDate | None, expected: str) -> None:
    """Test build_publication_date_filters function."""
    assert urls.build_publication_date_filters(from_date, to_date) == expected


def test_build_works_url_single_entity() -> None:
    """A single entity key produces a plain filter."""
    assert urls.build_works_url(urls.AUTHOR_FILTER_KEY, ["A0"]) == (
        "https://api.openalex.org/works?filter=author.id:A0&sort=publication_date&per-page=100"
    )


def test_build_works_url_joins_entities() -> None:
    """Several entity keys are joined with the OpenAlex OR separator."""
    assert urls.build_works_url(urls.INSTITUTION_FILTER_KEY, ["I0", "I1", "I2"]) == (
        "https://api.openalex.org/works?filter=institutions.id:I0|I1|I2&sort=publication_date&per-page=100"
    )


def test_build_works_url_with_dates() -> None:
    """Date filters land inside the filter parameter, before sorting."""
    assert urls.build_works_url(urls.AUTHOR_FILTER_KEY, ["A0"], FROM_DATE, TO_DATE) == (
        "https://api.openalex.org/works?filter=author.id:A0"
        ",from_publication_date:2020-01-02,to_publication_date:2023-11-30"
        "&sort=publication_date&per-page=100"
    )


def test_build_cited_by_url() -> None:
    """Test build_cited_by_url function."""
    assert urls.build_cited_by_url("W0") == ("https://api.openalex.org/works?filter=cites:W0&sort=publication_date&per-page=100")


def test_build_cited_by_url_with_dates() -> None:
    """Test build_cited_by_url function with a date range."""
    assert urls.build_cited_by_url("W0", FROM_DATE, TO_DATE) == (
        "https://api.openalex.org/works?filter=cites:W0"
        ",from_publication_date:2020-01-02,to_publication_date:2023-11-30"
        "&sort=publication_date&per-page=100"
    )


def test_build_source_url() -> None:
    """Test build_source_url function."""
    assert urls.build_source_url("S0") == "https://api.openalex.org/sources/S0"
