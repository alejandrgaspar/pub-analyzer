"""Test the report models from pub_analyzer/models/report.py."""

import json
from typing import Any

from pub_analyzer.models.report import AuthorReport, CitationReport, CitationType
from pub_analyzer.models.work import CitingWork, Work
from tests.data.builders import make_author_report, make_work

TOPIC_LEVEL = {"id": "https://openalex.org/fields/27", "display_name": "Medicine"}

CONCEPT = {
    "id": "https://openalex.org/C71924100",
    "wikidata": "https://www.wikidata.org/wiki/Q11190",
    "display_name": "Medicine",
    "level": 0,
    "score": 0.9187037,
}
"""A concept, as reports saved them before concepts were removed."""


def make_citing_work() -> Work:
    """Build a whole work, with something in each of the fields citing works leave out."""
    return make_work(
        "W2",
        title="Citing work",
        authors=["A1"],
        sources=["S1"],
        keywords=[{"id": "https://openalex.org/keywords/medicine", "display_name": "Medicine", "score": 0.5}],
        topics=[
            {
                "id": "https://openalex.org/T10001",
                "display_name": "Topic",
                "score": 0.9,
                "domain": TOPIC_LEVEL,
                "field": TOPIC_LEVEL,
                "subfield": TOPIC_LEVEL,
            }
        ],
        referenced_works=["https://openalex.org/W123"],
    )


def make_cited_report() -> AuthorReport:
    """Build an author report whose work is cited once."""
    report = make_author_report()
    report.works[0].cited_by = [CitationReport(work=make_citing_work(), citation_type=CitationType.TypeA)]
    return report


def test_citation_keeps_only_the_fields_of_a_citing_work() -> None:
    """A whole work given to a citation is cut down to a citing work, with the same values."""
    work = make_citing_work()

    citation = CitationReport(work=work, citation_type=CitationType.TypeA)

    assert type(citation.work) is CitingWork
    assert citation.work.model_dump() == work.model_dump(include=set(CitingWork.model_fields))


def test_saved_report_keeps_only_the_fields_of_citing_works() -> None:
    """Works keep all their fields when saved, and the works citing them only theirs."""
    saved = json.loads(make_cited_report().model_dump_json(by_alias=True))

    assert saved["works"][0]["work"].keys() == Work.model_fields.keys()
    assert saved["works"][0]["cited_by"][0]["work"].keys() == CitingWork.model_fields.keys()


def test_reports_saved_with_whole_citing_works_and_concepts_still_load() -> None:
    """Reports saved with whole citing works, and with concepts, load without the fields left out."""
    report = make_cited_report()
    saved: dict[str, Any] = report.model_dump(mode="json", by_alias=True)
    saved["works"][0]["work"]["concepts"] = [CONCEPT]
    saved["works"][0]["cited_by"][0]["work"] = make_citing_work().model_dump(mode="json") | {"concepts": [CONCEPT]}

    loaded = AuthorReport.model_validate_json(json.dumps(saved))

    assert type(loaded.works[0].work) is Work
    assert type(loaded.works[0].cited_by[0].work) is CitingWork
    assert loaded.model_dump() == report.model_dump()
