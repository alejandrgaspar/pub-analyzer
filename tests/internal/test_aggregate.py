"""Test report aggregation from pub_analyzer/internal/report/aggregate.py."""

import pytest
from pydantic import HttpUrl

from pub_analyzer.internal.report import aggregate
from pub_analyzer.models.author import DehydratedAuthor
from pub_analyzer.models.report import CitationType
from pub_analyzer.models.source import Source
from pub_analyzer.models.work import Authorship, OpenAccessStatus
from tests.data.builders import make_work
from tests.data.source import SOURCE


def test_get_authors_list() -> None:
    """Test get_authors_list function."""
    authorships = [
        Authorship(author_position="first", author=DehydratedAuthor(id=HttpUrl("https://openalex.org/A4356032281"))),
        Authorship(author_position="middle", author=DehydratedAuthor(id=HttpUrl("https://openalex.org/A2642025319"))),
        Authorship(author_position="last", author=DehydratedAuthor(id=HttpUrl("https://openalex.org/A4356881717"))),
    ]

    assert aggregate.get_authors_list(authorships=authorships) == ["A4356032281", "A2642025319", "A4356881717"]


def test_get_authors_list_empty() -> None:
    """A work with no authorship's yields no authors."""
    assert aggregate.get_authors_list(authorships=[]) == []


@pytest.mark.parametrize(
    ["original_authors", "cited_authors", "expected_cite_type"],
    [
        pytest.param(["A0", "A1"], ["A2", "A3"], CitationType.TypeA, id="no-overlap"),
        pytest.param(["A0", "A1"], ["A1", "A3"], CitationType.TypeB, id="shared-author"),
        pytest.param(["A0"], ["A0"], CitationType.TypeB, id="same-author"),
        pytest.param(["A0"], [], CitationType.TypeA, id="citing-work-without-authors"),
        pytest.param([], ["A0"], CitationType.TypeA, id="cited-work-without-authors"),
    ],
)
def test_get_citation_type(original_authors: list[str], cited_authors: list[str], expected_cite_type: CitationType) -> None:
    """Test get_citation_type function."""
    assert aggregate.get_citation_type(original_authors, cited_authors) == expected_cite_type


def test_build_work_report_classifies_citations() -> None:
    """Citations are classified and counted against the work's own authors."""
    work = make_work("W0", authors=["A0", "A1"])
    citing_works = [
        make_work("W1", authors=["A2"]),  # Type A
        make_work("W2", authors=["A1", "A9"]),  # Type B, shares A1
        make_work("W3", authors=["A3", "A4"]),  # Type A
    ]

    work_report = aggregate.build_work_report(work=work, citing_works=citing_works)

    assert [citation.citation_type for citation in work_report.cited_by] == [
        CitationType.TypeA,
        CitationType.TypeB,
        CitationType.TypeA,
    ]
    assert work_report.citation_summary.type_a_count == 2
    assert work_report.citation_summary.type_b_count == 1
    assert work_report.work.id == work.id


def test_build_work_report_without_citations() -> None:
    """A work nobody cites gets an empty, zeroed report."""
    work_report = aggregate.build_work_report(work=make_work("W0", authors=["A0"]), citing_works=[])

    assert work_report.cited_by == []
    assert work_report.citation_summary.type_a_count == 0
    assert work_report.citation_summary.type_b_count == 0


def test_summarize_citations() -> None:
    """Per-work citation counts add up into the report summary."""
    work_reports = [
        aggregate.build_work_report(make_work(authors=["A0"]), [make_work(authors=["A1"]), make_work(authors=["A0"])]),
        aggregate.build_work_report(make_work(authors=["A0"]), [make_work(authors=["A2"])]),
        aggregate.build_work_report(make_work(authors=["A0"]), []),
    ]

    summary = aggregate.summarize_citations(work_reports)

    assert summary.type_a_count == 2
    assert summary.type_b_count == 1


def test_summarize_citations_empty() -> None:
    """A report with no works has no citations."""
    summary = aggregate.summarize_citations([])

    assert summary.type_a_count == 0
    assert summary.type_b_count == 0


def test_summarize_open_access() -> None:
    """Test summarize_open_access function."""
    works = [
        make_work(oa_status=OpenAccessStatus.gold),
        make_work(oa_status=OpenAccessStatus.gold),
        make_work(oa_status=OpenAccessStatus.closed),
        make_work(oa_status=OpenAccessStatus.diamond),
        make_work(oa_status=OpenAccessStatus.green),
        make_work(oa_status=OpenAccessStatus.hybrid),
        make_work(oa_status=OpenAccessStatus.bronze),
    ]

    summary = aggregate.summarize_open_access(works)

    assert summary.model_dump() == {"diamond": 1, "gold": 2, "green": 1, "hybrid": 1, "bronze": 1, "closed": 1}


def test_summarize_open_access_empty() -> None:
    """Every counter stays at zero when there are no works."""
    assert aggregate.summarize_open_access([]).model_dump() == {
        "diamond": 0,
        "gold": 0,
        "green": 0,
        "hybrid": 0,
        "bronze": 0,
        "closed": 0,
    }


def test_summarize_work_types_keeps_first_appearance_order() -> None:
    """Counters follow the order each type is first seen, not alphabetical order."""
    works = [
        make_work(work_type="article"),
        make_work(work_type="book-chapter"),
        make_work(work_type="article"),
        make_work(work_type="book"),
        make_work(work_type="article"),
    ]

    summary = aggregate.summarize_work_types(works)

    assert [(counter.type_name, counter.count) for counter in summary] == [
        ("article", 3),
        ("book-chapter", 1),
        ("book", 1),
    ]


def test_summarize_work_types_empty() -> None:
    """No works, no counters."""
    assert aggregate.summarize_work_types([]) == []


def test_count_by_year() -> None:
    """Works count towards their own year, citations towards the citing work's year."""
    work_reports = [
        aggregate.build_work_report(
            make_work(publication_year=2020, authors=["A0"]),
            [make_work(publication_year=2021, authors=["A1"]), make_work(publication_year=2022, authors=["A2"])],
        ),
        aggregate.build_work_report(
            make_work(publication_year=2020, authors=["A0"]),
            [make_work(publication_year=2022, authors=["A3"])],
        ),
        aggregate.build_work_report(make_work(publication_year=2022, authors=["A0"]), []),
    ]

    assert aggregate.count_by_year(work_reports) == [
        aggregate.YearCount(year=2020, works_count=2, cited_by_count=0),
        aggregate.YearCount(year=2021, works_count=0, cited_by_count=1),
        aggregate.YearCount(year=2022, works_count=1, cited_by_count=2),
    ]


def test_count_by_year_is_sorted() -> None:
    """Years come out ascending regardless of the order works arrive in."""
    work_reports = [aggregate.build_work_report(make_work(publication_year=year, authors=["A0"]), []) for year in [2022, 1999, 2015, 2003]]

    assert [counts.year for counts in aggregate.count_by_year(work_reports)] == [1999, 2003, 2015, 2022]


def test_count_by_year_skips_works_without_year() -> None:
    """Works and citations with no publication year are left out."""
    work_reports = [
        aggregate.build_work_report(
            make_work(publication_year=None, authors=["A0"]),
            [make_work(publication_year=None, authors=["A1"]), make_work(publication_year=2021, authors=["A2"])],
        ),
    ]

    assert aggregate.count_by_year(work_reports) == [aggregate.YearCount(year=2021, works_count=0, cited_by_count=1)]


def test_count_by_year_empty() -> None:
    """No works, no year counts."""
    assert aggregate.count_by_year([]) == []


def test_collect_dehydrated_sources_deduplicates() -> None:
    """Each source appears once, in order of first appearance."""
    works = [
        make_work(sources=["S1", "S2"]),
        make_work(sources=["S2", "S3"]),
        make_work(sources=["S1"]),
    ]

    sources = aggregate.collect_dehydrated_sources(works)

    assert [str(source.id) for source in sources] == [
        "https://openalex.org/S1",
        "https://openalex.org/S2",
        "https://openalex.org/S3",
    ]


def test_collect_dehydrated_sources_ignores_locations_without_source() -> None:
    """Works with no located source contribute nothing."""
    assert aggregate.collect_dehydrated_sources([make_work(sources=[]), make_work(sources=[])]) == []


def _source_with_citedness(citedness: float) -> Source:
    """Build a Source carrying a given 2-year mean citedness."""
    payload = dict(SOURCE)
    payload["summary_stats"] = dict(SOURCE["summary_stats"]) | {"2yr_mean_citedness": citedness}

    return Source(**payload)


def test_build_sources_summary_sorts_by_citedness() -> None:
    """Sources come out ranked by 2-year mean citedness, descending."""
    sources = [_source_with_citedness(1.5), _source_with_citedness(9.0), _source_with_citedness(4.2)]

    summary = aggregate.build_sources_summary(sources)

    assert [source.summary_stats.two_yr_mean_citedness for source in summary.sources] == [9.0, 4.2, 1.5]


def test_build_sources_summary_empty() -> None:
    """An empty source list summarizes to an empty summary."""
    assert aggregate.build_sources_summary([]).sources == []
