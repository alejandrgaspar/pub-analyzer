"""Integration test of the make_report function from pub_analyzer/internal/report.py."""


import httpx
import pytest
from pydantic import BaseModel, TypeAdapter

from pub_analyzer.internal.report import make_author_report
from pub_analyzer.models.author import Author
from pub_analyzer.models.report import AuthorReport, CitationResume, OpenAccessResume, WorkTypeCounter


class ExpectedReportData(BaseModel):
    """Data expected in reports model."""

    citation_resume: CitationResume
    open_access_resume: OpenAccessResume
    works_type_resume: list[WorkTypeCounter]


@pytest.mark.asyncio
@pytest.mark.parametrize(
        ['author_openalex_id', 'expected_report'],
        [
            [
                "A5015201707",
                ExpectedReportData(
                    citation_resume = CitationResume(type_a_count=5, type_b_count=1),
                    open_access_resume = OpenAccessResume(gold=1, green=1, hybrid=0, bronze=0, closed=13),
                    works_type_resume=[WorkTypeCounter(type_name="article", count=15),],
                )
            ],
            [
                "A5088021854",
                ExpectedReportData(
                    citation_resume = CitationResume(type_a_count=3, type_b_count=1),
                    open_access_resume = OpenAccessResume(gold=4, green=0, hybrid=1, bronze=0, closed=7),
                    works_type_resume=[WorkTypeCounter(type_name="article", count=11), WorkTypeCounter(type_name="book-chapter", count=1)],
                )
            ],
            [
                "A5058237853",
                ExpectedReportData(
                    citation_resume = CitationResume(type_a_count=3, type_b_count=0),
                    open_access_resume = OpenAccessResume(gold=0, green=0, hybrid=1, bronze=1, closed=0),
                    works_type_resume=[WorkTypeCounter(type_name="article", count=1), WorkTypeCounter(type_name="book-chapter", count=1)],
                )
            ],
        ],
)
@pytest.mark.vcr
async def test_make_author_report(author_openalex_id: str, expected_report: ExpectedReportData) -> None:
    """Integration test of make_author_report function."""
    url = f"https://api.openalex.org/authors/{author_openalex_id}"
    async with httpx.AsyncClient() as client:
        result = (await client.get(url)).json()
        author: Author = TypeAdapter(Author).validate_python(result)

    report: AuthorReport = await make_author_report(author=author)

    # Assert report resumes are correct
    assert report.citation_resume.model_dump() == expected_report.citation_resume.model_dump()
    assert report.open_access_resume.model_dump() == expected_report.open_access_resume.model_dump()
    assert [work_type.model_dump() for work_type in report.works_type_resume] == [work_type.model_dump() for work_type in expected_report.works_type_resume]  # noqa: E501

    # Assert resume counts are equal to number of works
    assert sum([len(work.cited_by) for work in report.works]) == expected_report.citation_resume.type_a_count + expected_report.citation_resume.type_b_count  # noqa: E501
    assert sum([len(report.works)]) == sum(expected_report.open_access_resume.model_dump().values())
