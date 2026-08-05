"""Test builder functions from pub_analyzer/internal/report/builder.py."""

from typing import Any

import httpx
import pytest
import respx
from pydantic import HttpUrl

from pub_analyzer.internal import identifier
from pub_analyzer.internal.report import builder
from pub_analyzer.models.author import Author, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionResult, InstitutionType
from tests.data.author import AUTHOR
from tests.data.institution import INSTITUTION
from tests.data.source import SOURCE
from tests.data.work import WORK


def _dehydrated_author(author_id: str) -> DehydratedAuthor:
    """Build a DehydratedAuthor from a bare OpenAlex key."""
    return DehydratedAuthor(id=HttpUrl(f"https://openalex.org/{author_id}"))


def _dehydrated_institution(institution_id: str) -> DehydratedInstitution:
    """Build a DehydratedInstitution from a bare OpenAlex key."""
    return DehydratedInstitution(
        id=HttpUrl(f"https://openalex.org/{institution_id}"),
        ror="",
        display_name="",
        country_code="",
        type=InstitutionType.Education,
    )


@pytest.mark.parametrize(
    ["profiles", "expected_keys"],
    [
        pytest.param([_dehydrated_author("A0")], ["A0"], id="single-profile"),
        pytest.param(
            [_dehydrated_author("A0"), _dehydrated_author("A1"), _dehydrated_author("A2")],
            ["A0", "A1", "A2"],
            id="several-profiles",
        ),
        pytest.param([], [], id="no-profiles"),
    ],
)
def test_get_profiles_keys_for_authors(profiles: list[Author | AuthorResult | DehydratedAuthor], expected_keys: list[str]) -> None:
    """Test _get_profiles_keys function with author profiles."""
    assert builder._get_profiles_keys(profiles, identifier.get_author_id) == expected_keys


@pytest.mark.parametrize(
    ["profiles", "expected_keys"],
    [
        pytest.param([_dehydrated_institution("I0")], ["I0"], id="single-profile"),
        pytest.param(
            [_dehydrated_institution("I0"), _dehydrated_institution("I1"), _dehydrated_institution("I2")],
            ["I0", "I1", "I2"],
            id="several-profiles",
        ),
    ],
)
def test_get_profiles_keys_for_institutions(
    profiles: list[Institution | InstitutionResult | DehydratedInstitution], expected_keys: list[str]
) -> None:
    """Test _get_profiles_keys function with institution profiles."""
    assert builder._get_profiles_keys(profiles, identifier.get_institution_id) == expected_keys


def _mock_empty_report(respx_mock: respx.MockRouter) -> None:
    """Answer every works request with an empty page, so no report work is needed."""
    respx_mock.get(url__startswith="https://api.openalex.org/works").mock(
        return_value=httpx.Response(
            status_code=httpx.codes.OK,
            json={"meta": {"count": 0, "per_page": 100, "next_cursor": None}, "results": []},
        )
    )


@pytest.mark.asyncio
async def test_make_author_report_does_not_mutate_the_author() -> None:
    """The Author passed in keeps the counts it arrived with."""
    author = Author(**AUTHOR)
    original_counts = [counts.model_copy() for counts in author.counts_by_year]

    with respx.mock(assert_all_called=True) as respx_mock:
        _mock_empty_report(respx_mock)
        report = await builder.make_author_report(author=author)

    assert author.counts_by_year == original_counts, "the caller's Author was modified"
    assert report.author is not author
    # No works means no year counts observed, which is what the report must carry.
    assert report.author.counts_by_year == []


@pytest.mark.asyncio
async def test_make_institution_report_does_not_mutate_the_institution() -> None:
    """The Institution passed in keeps the counts it arrived with."""
    institution = Institution(**INSTITUTION)
    original_counts = [counts.model_copy() for counts in institution.counts_by_year]

    with respx.mock(assert_all_called=True) as respx_mock:
        _mock_empty_report(respx_mock)
        report = await builder.make_institution_report(institution=institution)

    assert institution.counts_by_year == original_counts, "the caller's Institution was modified"
    assert report.institution is not institution
    assert report.institution.counts_by_year == []


SOURCE_KEY = "S137773608"

LOCATION = {
    "is_oa": False,
    "landing_page_url": "https://example.org/work",
    "license": None,
    "pdf_url": None,
    "version": None,
    "source": {
        "id": f"https://openalex.org/{SOURCE_KEY}",
        "display_name": "Nature",
        "issn_l": None,
        "issn": None,
        "is_oa": False,
        "is_in_doaj": False,
        "host_organization": None,
        "type": "journal",
    },
}


def _works_page(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a single, final page of works."""
    return {"meta": {"count": len(results), "per_page": 100, "next_cursor": None}, "results": results}


@pytest.mark.asyncio
async def test_make_author_report_end_to_end() -> None:
    """Drive the whole pipeline offline: works, their citations, and their sources."""
    author_work = dict(WORK) | {"publication_year": 2020, "locations": [LOCATION]}
    citing_work = dict(WORK) | {
        "id": "https://openalex.org/W999",
        "ids": {"openalex": "https://openalex.org/W999"},
        "publication_year": 2022,
        "authorships": [{"author_position": "first", "author": {"id": "https://openalex.org/A999", "display_name": "Someone"}}],
    }

    def works_handler(request: httpx.Request) -> httpx.Response:
        """Serve the author's works, then the works citing each of them."""
        works_filter = request.url.params.get("filter", "")
        results = [author_work] if works_filter.startswith("author.id:") else [citing_work]

        return httpx.Response(status_code=httpx.codes.OK, json=_works_page(results))

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith="https://api.openalex.org/works").mock(side_effect=works_handler)
        respx_mock.get(url__startswith=f"https://api.openalex.org/sources/{SOURCE_KEY}").mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=dict(SOURCE))
        )

        report = await builder.make_author_report(author=Author(**AUTHOR))

    assert len(report.works) == 1
    assert len(report.works[0].cited_by) == 1
    # The citing author shares nobody with the cited work, so the citation is Type A.
    assert report.citation_summary.type_a_count == 1
    assert report.citation_summary.type_b_count == 0

    assert [source.id for source in report.sources_summary.sources] == [HttpUrl(f"https://openalex.org/{SOURCE_KEY}")]
    assert [counts.model_dump() for counts in report.author.counts_by_year] == [
        {"year": 2020, "works_count": 1, "cited_by_count": 0},
        {"year": 2022, "works_count": 0, "cited_by_count": 1},
    ]


@pytest.mark.asyncio
async def test_make_author_report_survives_an_unreachable_source() -> None:
    """A source that cannot be retrieved is skipped, not fatal."""
    author_work = dict(WORK) | {"locations": [LOCATION]}

    def works_handler(request: httpx.Request) -> httpx.Response:
        """Serve one work, then no citations for it."""
        works_filter = request.url.params.get("filter", "")
        results = [author_work] if works_filter.startswith("author.id:") else []

        return httpx.Response(status_code=httpx.codes.OK, json=_works_page(results))

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith="https://api.openalex.org/works").mock(side_effect=works_handler)
        respx_mock.get(url__startswith=f"https://api.openalex.org/sources/{SOURCE_KEY}").mock(
            return_value=httpx.Response(status_code=httpx.codes.NOT_FOUND)
        )

        report = await builder.make_author_report(author=Author(**AUTHOR))

    assert len(report.works) == 1
    assert report.sources_summary.sources == []


@pytest.mark.asyncio
async def test_make_author_report_keeps_the_author_details() -> None:
    """Replacing the year counts leaves every other field untouched."""
    author = Author(**AUTHOR)

    with respx.mock(assert_all_called=True) as respx_mock:
        _mock_empty_report(respx_mock)
        report = await builder.make_author_report(author=author)

    assert report.author.id == author.id
    assert report.author.display_name == author.display_name
    assert report.author.works_count == author.works_count
