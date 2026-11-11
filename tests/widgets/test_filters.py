"""Test the date filters on the author and institution summaries."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import httpx2 as httpx
import pytest
from textual.pilot import Pilot
from textual.widgets import Button, Checkbox, Collapsible

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.author.core import AuthorSummaryWidget
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.common.filters import DateRangeFilter
from pub_analyzer.widgets.common.input import DateInput
from pub_analyzer.widgets.common.summary import SummaryWidget
from pub_analyzer.widgets.institution.core import InstitutionSummaryWidget
from pub_analyzer.widgets.report import core
from pub_analyzer.widgets.search import FinderWidget
from tests import http_mock
from tests.data.author import AUTHOR, AUTHOR_RESULT_OBJECT
from tests.data.builders import make_author_report, make_institution_report
from tests.data.institution import INSTITUTION, INSTITUTION_RESULT_OBJECT
from tests.widgets.helpers import wait_for_workers


@dataclass
class Entity:
    """What differs between the author and the institution summaries."""

    name: str
    """`author` or `institution`, as used in OpenAlex URLs and widget ids."""
    make_summary: Callable[[], SummaryWidget]
    details: dict[str, Any]
    """What OpenAlex returns for the entity."""
    make_report: Callable[[], AuthorReport | InstitutionReport]
    report_widget: type[core.AuthorReportWidget] | type[core.InstitutionReportWidget]


AN_AUTHOR = Entity(
    name="author",
    make_summary=lambda: AuthorSummaryWidget(AUTHOR_RESULT_OBJECT),
    details=AUTHOR,
    make_report=make_author_report,
    report_widget=core.AuthorReportWidget,
)
AN_INSTITUTION = Entity(
    name="institution",
    make_summary=lambda: InstitutionSummaryWidget(INSTITUTION_RESULT_OBJECT),
    details=INSTITUTION,
    make_report=make_institution_report,
    report_widget=core.InstitutionReportWidget,
)


def openalex_returning(entity: Entity) -> http_mock.MockRouter:
    """Mock OpenAlex so it returns the entity's details."""
    router = http_mock.mock()
    router.get(url__startswith=f"https://api.openalex.org/{entity.name}s/").mock(return_value=httpx.Response(200, json=entity.details))
    return router


async def show_summary(pilot: Pilot, entity: Entity) -> SummaryWidget:
    """Show the entity's summary in place of the search page, and wait for its details to load."""
    summary = entity.make_summary()
    await pilot.app.query_one(FinderWidget).remove()
    await pilot.app.query_one(MainContent).mount(summary)
    await wait_for_workers(pilot)
    return summary


async def enable_publication_date_filter(pilot: Pilot, summary: SummaryWidget, entity: Entity) -> DateRangeFilter:
    """Open the report filters and tick the publication date range, with the keyboard."""
    filters = summary.query_one(Collapsible)
    title = filters.query_one("CollapsibleTitle")
    title.scroll_visible(animate=False)
    title.focus()
    await pilot.press("enter")
    assert not filters.collapsed

    date_filter = summary.query_one(f"#{entity.name}-date-range-filter", DateRangeFilter)
    checkbox = date_filter.query_one(Checkbox)
    checkbox.scroll_visible(animate=False)
    checkbox.focus()
    await pilot.press("space")

    assert not date_filter.filter_disabled
    return date_filter


async def set_dates(pilot: Pilot, date_filter: DateRangeFilter, start: str | None = None, end: str | None = None) -> None:
    """Fill in the filter's dates.

    Setting the values posts the same validated `Changed` messages as typing, without paying
    ~0.1s per simulated key press.
    """
    if start is not None:
        date_filter.query_one("#from-date", DateInput).value = start
    if end is not None:
        date_filter.query_one("#to-date", DateInput).value = end
    await pilot.pause()


@pytest.mark.asyncio
async def test_report_is_blocked_until_both_dates_are_valid() -> None:
    """With the date filter on, Make Report is disabled until the range has two valid dates."""
    with openalex_returning(AN_AUTHOR):
        async with PubAnalyzerApp().run_test(size=(140, 70)) as pilot:
            summary = await show_summary(pilot, AN_AUTHOR)
            make_report = summary.query_one("#make-report-button", Button)
            assert not make_report.disabled

            # Turning the filter on blocks the report until the range is complete.
            date_filter = await enable_publication_date_filter(pilot, summary, AN_AUTHOR)
            assert make_report.disabled

            await set_dates(pilot, date_filter, start="2020-01-01")
            assert date_filter.from_date == datetime(2020, 1, 1)
            assert make_report.disabled

            # An impossible date doesn't count.
            await set_dates(pilot, date_filter, end="2020-99-01")
            assert date_filter.to_date is None
            assert make_report.disabled

            # Two valid dates unblock it.
            await set_dates(pilot, date_filter, end="2020-12-31")
            assert date_filter.to_date == datetime(2020, 12, 31)
            assert not make_report.disabled


@pytest.mark.asyncio
@pytest.mark.parametrize("entity", [pytest.param(AN_AUTHOR, id="author"), pytest.param(AN_INSTITUTION, id="institution")])
async def test_report_is_built_with_the_chosen_dates(entity: Entity, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make Report passes the publication dates to the report builder, then shows the report."""
    report = entity.make_report()
    build_report = AsyncMock(return_value=report)
    monkeypatch.setattr(core, f"make_{entity.name}_report", build_report)

    with openalex_returning(entity):
        async with PubAnalyzerApp().run_test(size=(140, 70)) as pilot:
            summary = await show_summary(pilot, entity)
            date_filter = await enable_publication_date_filter(pilot, summary, entity)
            await set_dates(pilot, date_filter, start="2020-01-01", end="2020-12-31")

            # Make the report.
            make_report = summary.query_one("#make-report-button", Button)
            make_report.scroll_visible(animate=False)
            await pilot.pause()
            assert await pilot.click(make_report)
            await wait_for_workers(pilot)

            # The report replaces the summary.
            assert not pilot.app.query(type(summary))
            assert pilot.app.query_one(entity.report_widget).report == report

    # Only the publication dates were filtered.
    build_report.assert_awaited_once()
    arguments = build_report.call_args.kwargs
    assert arguments[entity.name].display_name == entity.details["display_name"]
    assert (arguments["pub_from_date"], arguments["pub_to_date"]) == (datetime(2020, 1, 1), datetime(2020, 12, 31))
    assert (arguments["cited_from_date"], arguments["cited_to_date"]) == (None, None)
