"""Test report functions from pub_analyzer/internal/report.py."""

import copy
import math
from typing import Any

import httpx
import pytest
import respx
from pydantic import HttpUrl

from pub_analyzer.internal import report
from pub_analyzer.models.author import DehydratedAuthor
from pub_analyzer.models.report import CitationType
from pub_analyzer.models.work import Authorship
from tests.data.work import WORK


def test_get_authors_list() -> None:
    """Test _get_authors_list function."""
    frist_author = DehydratedAuthor(id=HttpUrl("https://openalex.org/A4356032281"))
    middle_author = DehydratedAuthor(id=HttpUrl("https://openalex.org/A2642025319"))
    last_author = DehydratedAuthor(id=HttpUrl("https://openalex.org/A4356881717"))

    authorships = [
        Authorship(
            author_position='first',
            author=frist_author
        ),
        Authorship(
            author_position='middle',
            author=middle_author
        ),
        Authorship(
            author_position='last',
            author=last_author
        ),
    ]

    open_ids_list = report._get_authors_list(authorships=authorships)
    assert open_ids_list == ["A4356032281", "A2642025319", "A4356881717"]


@pytest.mark.parametrize(
        ['original_authors', 'cited_authors', 'expected_cite_type'],
        [
            [("A4358557189", "A2750800828"), ("A4356997054", "A4354328133"), CitationType.TypeA],
            [("A4358557189", "A2750800828"), ("A2750800828", "A4354328133"), CitationType.TypeB],
        ]
)
def test_get_citation_type(original_authors: list[str], cited_authors: list[str], expected_cite_type: CitationType) -> None:
    """Test _get_citation_type function."""
    function_cite_type = report._get_citation_type(original_authors, cited_authors)

    assert function_cite_type == expected_cite_type


@pytest.mark.parametrize(
        ['works', 'expected_works'],
        [
            [
                [
                    {'title': 'Title1', 'language': 'en'},
                    {'title': 'Title2', 'language': None},
                    {'title': None, 'language': 'es'}
                ],
                [
                    {'title': 'Title1', 'language': 'en'},
                    {'title': 'Title2', 'language': None},
                ],
            ],
        ]
)
def test_get_valid_works(works: list[dict[str, Any]], expected_works: list[dict[str, Any]]) -> None:
    """Test _get_valid_works function."""
    assert report._get_valid_works(works) == expected_works


@pytest.mark.asyncio
@pytest.mark.parametrize(
        ['author_id', 'works'],
        [
            ["A4356881717", {"meta": {"count": 2, "page": 1, "per_page": 5}, "results": [WORK, WORK]}],
            ["A4356881717", {"meta": {"count": 10, "page": 1, "per_page": 5}, "results": [WORK for _ in range(4)]}],
            ["A4356881717", {"meta": {"count": 15, "page": 1, "per_page": 5}, "results": [WORK for _ in range(4)]}]
        ]
)
async def test_get_works(author_id: str, works: dict[str, Any]) -> None:
    """Test _get_works function."""
    base_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_date"

    with respx.mock(assert_all_called=True, assert_all_mocked=True) as respx_mock:
        respx_mock.get(base_url).mock(return_value=httpx.Response(
                status_code=httpx.codes.OK,
                json=works
            )
        )

        # Test case when iteration over pages is needed
        page_count = math.ceil(works["meta"]["count"] / works["meta"]["per_page"])
        for page in range(1, page_count):
            page_number = page + 1
            work_new_page = copy.copy(works)
            work_new_page['meta']['page'] = page_number

            respx_mock.get(base_url + f"&page={page_number}").mock(return_value=httpx.Response(
                    status_code=httpx.codes.OK,
                    json=work_new_page
                )
            )

        client = httpx.AsyncClient()
        await report._get_works(url=base_url, client=client)
