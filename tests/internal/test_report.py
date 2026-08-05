"""Test builder functions from pub_analyzer/internal/report/builder.py."""

import copy
import math
from typing import Any

import httpx
import pytest
import respx
from pydantic import HttpUrl

from pub_analyzer.internal.limiter import RateLimiter
from pub_analyzer.internal.report import builder
from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionOpenAlexKey, InstitutionResult, InstitutionType
from tests.data.work import WORK


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
    ["main_author", "extra_profiles", "expected_keys"],
    [
        pytest.param(DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")), None, ["A0"], id="no-extra-profiles"),
        pytest.param(DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")), [], ["A0"], id="empty-extra-profiles"),
        pytest.param(
            DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")),
            [
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A1")),
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A2")),
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A3")),
            ],
            ["A0", "A1", "A2", "A3"],
            id="with-extra-profiles",
        ),
    ],
)
def test_get_author_profiles_keys(
    main_author: Author, extra_profiles: list[Author | AuthorResult | DehydratedAuthor] | None, expected_keys: list[AuthorOpenAlexKey]
) -> None:
    """Test _get_author_profiles_keys function."""
    assert builder._get_author_profiles_keys(main_author, extra_profiles) == expected_keys


@pytest.mark.parametrize(
    ["main_institution", "extra_profiles", "expected_keys"],
    [
        pytest.param(_dehydrated_institution("I0"), None, ["I0"], id="no-extra-profiles"),
        pytest.param(_dehydrated_institution("I0"), [], ["I0"], id="empty-extra-profiles"),
        pytest.param(
            _dehydrated_institution("I0"),
            [_dehydrated_institution("I1"), _dehydrated_institution("I2"), _dehydrated_institution("I3")],
            ["I0", "I1", "I2", "I3"],
            id="with-extra-profiles",
        ),
    ],
)
def test_get_institution_keys(
    main_institution: Institution,
    extra_profiles: list[Institution | InstitutionResult | DehydratedInstitution] | None,
    expected_keys: list[InstitutionOpenAlexKey],
) -> None:
    """Test _get_institution_keys function."""
    assert builder._get_institution_keys(main_institution, extra_profiles) == expected_keys


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["author_id", "works"],
    [
        ["A4356881717", {"meta": {"count": 2, "page": 1, "per_page": 5}, "results": [WORK, WORK]}],
        ["A4356881717", {"meta": {"count": 10, "page": 1, "per_page": 5}, "results": [WORK for _ in range(4)]}],
        ["A4356881717", {"meta": {"count": 15, "page": 1, "per_page": 5}, "results": [WORK for _ in range(4)]}],
    ],
)
async def test_get_works(author_id: str, works: dict[str, Any]) -> None:
    """Test _get_works function."""
    base_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_date"

    with respx.mock(assert_all_called=True, assert_all_mocked=True) as respx_mock:
        respx_mock.get(base_url).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json=works))

        # Test case when iteration over pages is needed
        page_count = math.ceil(works["meta"]["count"] / works["meta"]["per_page"])
        for page in range(1, page_count):
            page_number = page + 1
            work_new_page = copy.copy(works)
            work_new_page["meta"]["page"] = page_number

            respx_mock.get(base_url + f"&page={page_number}").mock(
                return_value=httpx.Response(status_code=httpx.codes.OK, json=work_new_page)
            )

        client = httpx.AsyncClient()
        limiter = RateLimiter(rate=8, per_second=1.0)
        retrieved_works = await builder._get_works(url=base_url, client=client, limiter=limiter)

    assert len(retrieved_works) == page_count * len(works["results"])


@pytest.mark.asyncio
async def test_get_works_raises_on_error_status() -> None:
    """An error status on the first page surfaces as an HTTPStatusError."""
    base_url = "https://api.openalex.org/works?filter=author.id:A0&sort=publication_date"

    with respx.mock(assert_all_called=True, assert_all_mocked=True) as respx_mock:
        respx_mock.get(base_url).mock(return_value=httpx.Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR))

        client = httpx.AsyncClient()
        limiter = RateLimiter(rate=8, per_second=1.0)

        with pytest.raises(httpx.HTTPStatusError):
            await builder._get_works(url=base_url, client=client, limiter=limiter)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["homepage_url", "expected_homepage_url"],
    [
        pytest.param("https://example.org", "https://example.org/", id="valid-url-kept"),
        pytest.param("www.example.org", None, id="schemeless-url-discarded"),
        pytest.param(None, None, id="missing-url"),
    ],
)
async def test_get_source_homepage_url(homepage_url: str | None, expected_homepage_url: str | None) -> None:
    """Sources carrying a homepage URL without scheme have it discarded."""
    from tests.data.source import SOURCE

    url = "https://api.openalex.org/sources/S137773608"
    payload = dict(SOURCE) | {"homepage_url": homepage_url}

    with respx.mock(assert_all_called=True, assert_all_mocked=True) as respx_mock:
        respx_mock.get(url).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json=payload))

        client = httpx.AsyncClient()
        limiter = RateLimiter(rate=8, per_second=1.0)
        source = await builder._get_source(url=url, client=client, limiter=limiter)

    assert (str(source.homepage_url) if source.homepage_url else None) == expected_homepage_url
