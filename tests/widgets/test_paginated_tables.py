"""Test moving between the pages of the report tables."""

from collections.abc import Callable

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, Label

from pub_analyzer.models.report import AuthorReport, CitationReport, CitationSummary, CitationType, WorkReport
from pub_analyzer.widgets.common import PaginatedTable
from pub_analyzer.widgets.report.source import SourcesTable
from pub_analyzer.widgets.report.work import WorksTable
from tests.data.builders import make_author_report, make_report_source, make_work
from tests.widgets.helpers import WidgetApp, click_when_ready, open_work_details

PAGE_SIZE = PaginatedTable.PAGE_SIZE
PAGER_BUTTONS = ("first-page", "previous-page", "next-page", "last-page")


def make_report(works_count: int, cited_works: range | None = None) -> AuthorReport:
    """Build an author report with many works.

    Args:
        works_count: Number of works in the report.
        cited_works: Positions of the works that have been cited. None of them, when omitted.
    """
    cited_works = cited_works if cited_works is not None else range(0)
    report = make_author_report()
    report.works = [
        WorkReport(
            work=make_work(f"W{idx}", title=f"Work {idx}"),
            cited_by=[CitationReport(work=make_work(), citation_type=CitationType.TypeA)] if idx in cited_works else [],
            citation_summary=CitationSummary(),
        )
        for idx in range(works_count)
    ]
    return report


def make_works_table(rows: int) -> PaginatedTable:
    """Build a works table listing as many works."""
    return WorksTable(make_report(rows))


def make_sources_table(rows: int) -> PaginatedTable:
    """Build a sources table listing as many sources."""
    return SourcesTable([make_report_source(f"S{idx}", f"Source {idx}") for idx in range(rows)])


TABLES = [
    pytest.param(make_works_table, id="works"),
    pytest.param(make_sources_table, id="sources"),
]


def page_label(table: PaginatedTable) -> str:
    """Return the text describing the page shown."""
    return str(table.query_one("#page-label", Label).render())


def disabled_buttons(table: PaginatedTable) -> set[str]:
    """Return the ids of the pager buttons that are disabled."""
    return {button_id for button_id in PAGER_BUTTONS if table.query_one(f"#{button_id}", Button).disabled}


async def click_pager_button(pilot: Pilot, table: PaginatedTable, button_id: str) -> None:
    """Scroll down to a pager button below the table, and click it."""
    button = table.query_one(f"#{button_id}", Button)
    button.scroll_visible(animate=False)
    await pilot.pause()

    await click_when_ready(pilot, button)
    await pilot.pause()


@pytest.mark.asyncio
@pytest.mark.parametrize("make_table", TABLES)
async def test_pager_moves_between_pages(make_table: Callable[[int], PaginatedTable]) -> None:
    """Each button shows its page, and the buttons that lead past the first or last page are disabled."""
    table = make_table(2 * PAGE_SIZE + 20)
    rows_name = table.ROWS_NAME
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        await pilot.pause()
        assert table.page_rows == range(0, PAGE_SIZE)
        assert page_label(table) == f"Page 1 of 3 · {rows_name} 1-50 of 120"
        assert disabled_buttons(table) == {"first-page", "previous-page"}

        await click_pager_button(pilot, table, "next-page")
        assert table.page_rows == range(PAGE_SIZE, 2 * PAGE_SIZE)
        assert page_label(table) == f"Page 2 of 3 · {rows_name} 51-100 of 120"
        assert disabled_buttons(table) == set()

        await click_pager_button(pilot, table, "last-page")
        assert table.page_rows == range(2 * PAGE_SIZE, 2 * PAGE_SIZE + 20)
        assert page_label(table) == f"Page 3 of 3 · {rows_name} 101-120 of 120"
        assert disabled_buttons(table) == {"next-page", "last-page"}

        await click_pager_button(pilot, table, "previous-page")
        assert table.page_rows == range(PAGE_SIZE, 2 * PAGE_SIZE)

        await click_pager_button(pilot, table, "first-page")
        assert table.page_rows == range(0, PAGE_SIZE)


@pytest.mark.asyncio
@pytest.mark.parametrize("make_table", TABLES)
async def test_pager_is_hidden_when_every_row_fits_on_one_page(make_table: Callable[[int], PaginatedTable]) -> None:
    """A table with a page of rows or fewer shows them all, without the pager."""
    table = make_table(PAGE_SIZE)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        await pilot.pause()
        assert table.page_rows == range(0, PAGE_SIZE)
        assert not table.query_one(".table-pager").display


@pytest.mark.asyncio
async def test_works_on_later_pages_open_their_own_details() -> None:
    """Clicking a work on a later page opens that work, and the page starts at the top of the table."""
    report = make_report(2 * PAGE_SIZE)
    table = WorksTable(report)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        await click_pager_button(pilot, table, "next-page")

        details = await open_work_details(pilot, table, idx=PAGE_SIZE)
        assert details.work_report is report.works[PAGE_SIZE]


@pytest.mark.asyncio
async def test_hiding_empty_works_pages_through_cited_works_only() -> None:
    """Without empty works, the pages list only cited works, which keep their position in the report."""
    table = WorksTable(make_report(2 * PAGE_SIZE + 20, cited_works=range(1, 2 * PAGE_SIZE + 20, 2)), show_empty_works=False)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        await pilot.pause()
        assert table.page_work_indexes == list(range(1, 2 * PAGE_SIZE, 2))
        assert page_label(table) == "Page 1 of 2 · Works 1-50 of 60"

        await click_pager_button(pilot, table, "next-page")
        assert table.page_work_indexes == list(range(2 * PAGE_SIZE + 1, 2 * PAGE_SIZE + 20, 2))
        assert page_label(table) == "Page 2 of 2 · Works 51-60 of 60"
