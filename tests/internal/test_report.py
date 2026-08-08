"""Test builder functions from pub_analyzer/internal/report/builder.py."""

from typing import Any

import httpx
import pytest
import respx
from pydantic import HttpUrl

from pub_analyzer.internal import identifier
from pub_analyzer.internal.report import builder
from pub_analyzer.internal.report.progress import ReportProgress, ReportStage
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
async def test_uncited_works_cost_no_request() -> None:
    """A work OpenAlex reports as never cited is not queried at all."""
    uncited = dict(WORK) | {"cited_by_count": 0, "locations": []}

    with respx.mock(assert_all_called=True) as respx_mock:
        works_route = respx_mock.get(url__startswith="https://api.openalex.org/works").mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=_works_page([uncited]))
        )

        report = await builder.make_author_report(author=Author(**AUTHOR))

    # Only the request listing the author's works, none for its citations.
    assert works_route.call_count == 1
    assert all(not call.request.url.params["filter"].startswith("cites:") for call in works_route.calls)
    assert report.works[0].cited_by == []
    assert report.citation_summary.type_a_count == 0


@pytest.mark.asyncio
async def test_cited_works_are_still_queried() -> None:
    """The shortcut must not swallow works that do have citations."""
    cited = dict(WORK) | {"cited_by_count": 5, "locations": []}

    def works_handler(request: httpx.Request) -> httpx.Response:
        """Serve the author's works, then the works citing them."""
        works_filter = request.url.params.get("filter", "")
        results = [cited] if works_filter.startswith("author.id:") else []

        return httpx.Response(status_code=httpx.codes.OK, json=_works_page(results))

    with respx.mock(assert_all_called=True) as respx_mock:
        works_route = respx_mock.get(url__startswith="https://api.openalex.org/works").mock(side_effect=works_handler)

        await builder.make_author_report(author=Author(**AUTHOR))

    assert any(call.request.url.params["filter"].startswith("cites:") for call in works_route.calls)


@pytest.mark.asyncio
async def test_works_reports_keep_their_order_under_concurrency() -> None:
    """Requests overlap, but the reports come back in the order the works arrived."""
    works = [
        dict(WORK) | {"id": f"https://openalex.org/W{index}", "ids": {"openalex": f"https://openalex.org/W{index}"}, "locations": []}
        for index in range(10)
    ]

    def works_handler(request: httpx.Request) -> httpx.Response:
        """Serve the author's works, then a citation carrying the cited work's key."""
        works_filter = request.url.params.get("filter", "")
        if works_filter.startswith("author.id:"):
            return httpx.Response(status_code=httpx.codes.OK, json=_works_page(works))

        cited_key = works_filter.removeprefix("cites:")
        citing = dict(WORK) | {
            "id": f"https://openalex.org/C{cited_key}",
            "ids": {"openalex": f"https://openalex.org/C{cited_key}"},
            "authorships": [{"author_position": "first", "author": {"id": "https://openalex.org/A999"}}],
        }

        return httpx.Response(status_code=httpx.codes.OK, json=_works_page([citing]))

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith="https://api.openalex.org/works").mock(side_effect=works_handler)

        report = await builder.make_author_report(author=Author(**AUTHOR))

    assert [str(work_report.work.id) for work_report in report.works] == [f"https://openalex.org/W{index}" for index in range(10)]
    # Each citation names the work it cites, so a shuffle would show up here too.
    assert [str(work_report.cited_by[0].work.id) for work_report in report.works] == [
        f"https://openalex.org/CW{index}" for index in range(10)
    ]


@pytest.mark.asyncio
async def test_report_progress_is_reported_in_order() -> None:
    """Every stage is announced, and each one counts up to its own total."""
    author_work = dict(WORK) | {"cited_by_count": 1, "locations": [LOCATION]}

    def works_handler(request: httpx.Request) -> httpx.Response:
        """Serve one work, then one work citing it."""
        works_filter = request.url.params.get("filter", "")
        results = [author_work] if works_filter.startswith("author.id:") else [dict(WORK)]

        return httpx.Response(status_code=httpx.codes.OK, json=_works_page(results))

    updates: list[ReportProgress] = []

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith="https://api.openalex.org/works").mock(side_effect=works_handler)
        respx_mock.get(url__startswith=f"https://api.openalex.org/sources/{SOURCE_KEY}").mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=dict(SOURCE))
        )

        await builder.make_author_report(author=Author(**AUTHOR), on_progress=updates.append)

    assert [update.stage for update in updates] == [
        ReportStage.works,
        ReportStage.citations,
        ReportStage.citations,
        ReportStage.sources,
        ReportStage.sources,
    ]
    # Each measured stage starts at zero and finishes at its total.
    assert [(update.done, update.total) for update in updates[1:]] == [(0, 1), (1, 1), (0, 1), (1, 1)]
    assert updates[-1].description == "Retrieving sources 1/1"


@pytest.mark.asyncio
async def test_skipped_sources_still_advance_progress() -> None:
    """A source that cannot be retrieved must not leave the bar short of its total."""
    author_work = dict(WORK) | {"cited_by_count": 0, "locations": [LOCATION]}

    updates: list[ReportProgress] = []

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith="https://api.openalex.org/works").mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=_works_page([author_work]))
        )
        respx_mock.get(url__startswith=f"https://api.openalex.org/sources/{SOURCE_KEY}").mock(
            return_value=httpx.Response(status_code=httpx.codes.NOT_FOUND)
        )

        report = await builder.make_author_report(author=Author(**AUTHOR), on_progress=updates.append)

    assert report.sources_summary.sources == []

    sources_updates = [update for update in updates if update.stage is ReportStage.sources]
    assert sources_updates[-1].done == sources_updates[-1].total == 1


@pytest.mark.asyncio
async def test_report_works_without_a_progress_callback() -> None:
    """The callback is optional."""
    with respx.mock(assert_all_called=True) as respx_mock:
        _mock_empty_report(respx_mock)
        report = await builder.make_author_report(author=Author(**AUTHOR))

    assert report.works == []


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
