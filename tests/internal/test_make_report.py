"""Integration test of the make_report function from pub_analyzer/internal/report.py."""

import httpx
import pytest
from pydantic import BaseModel, TypeAdapter

from pub_analyzer.internal.report import make_author_report
from pub_analyzer.models.author import Author
from pub_analyzer.models.report import AuthorReport, CitationSummary, OpenAccessSummary, WorkTypeCounter


class ExpectedReportData(BaseModel):
    """Data expected in reports model."""

    citation_summary: CitationSummary
    open_access_summary: OpenAccessSummary
    works_type_summary: list[WorkTypeCounter]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["author_openalex_id", "expected_report"],
    [
        [
            "A5015201707",
            ExpectedReportData(
                citation_summary=CitationSummary(type_a_count=5, type_b_count=1),
                open_access_summary=OpenAccessSummary(diamond=1, gold=2, green=1, hybrid=0, bronze=0, closed=14),
                works_type_summary=[
                    WorkTypeCounter(type_name="article", count=17),
                    WorkTypeCounter(type_name="book-chapter", count=1),
                ],
            ),
        ],
        [
            "A5088021854",
            ExpectedReportData(
                citation_summary=CitationSummary(type_a_count=11, type_b_count=2),
                open_access_summary=OpenAccessSummary(diamond=3, gold=3, green=0, hybrid=1, bronze=0, closed=8),
                works_type_summary=[WorkTypeCounter(type_name="article", count=14), WorkTypeCounter(type_name="book-chapter", count=1)],
            ),
        ],
        [
            "A5058237853",
            ExpectedReportData(
                citation_summary=CitationSummary(type_a_count=7, type_b_count=0),
                open_access_summary=OpenAccessSummary(gold=0, green=0, hybrid=1, bronze=1, closed=0),
                works_type_summary=[WorkTypeCounter(type_name="article", count=1), WorkTypeCounter(type_name="book-chapter", count=1)],
            ),
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

    # report: AuthorReport = await make_author_report(author=author)

    # # Assert report summary is correct
    # assert report.citation_summary.model_dump() == expected_report.citation_summary.model_dump()
    # assert report.open_access_summary.model_dump() == expected_report.open_access_summary.model_dump()
    # assert [work_type.model_dump() for work_type in report.works_type_summary] == [
    #     work_type.model_dump() for work_type in expected_report.works_type_summary
    # ]

    # # Assert summary counts are equal to number of works
    # assert (
    #     sum([len(work.cited_by) for work in report.works])
    #     == expected_report.citation_summary.type_a_count + expected_report.citation_summary.type_b_count
    # )
    # assert sum([len(report.works)]) == sum(expected_report.open_access_summary.model_dump().values())
