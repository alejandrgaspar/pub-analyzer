"""Test report functions from pub_analyzer/utils/report.py."""

import pytest
from pydantic import HttpUrl

from pub_analyzer.models.author import DehydratedAuthor
from pub_analyzer.models.report import CitationType
from pub_analyzer.models.work import Authorship
from pub_analyzer.utils import report


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
def test_get_citation_type(original_authors: list[str], cited_authors: list[str], expected_cite_type: CitationType) -> None:  # noqa: E501
    """Test _get_citation_type function."""
    function_cite_type = report._get_citation_type(original_authors, cited_authors)

    assert function_cite_type == expected_cite_type
