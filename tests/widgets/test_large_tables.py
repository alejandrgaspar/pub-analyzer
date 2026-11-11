"""Test that the report tables stay responsive when they have many rows."""

import time
from collections.abc import Callable

import pytest
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from textual.pilot import Pilot
from textual.widget import Widget

from pub_analyzer.models.report import CitationReport, CitationSummary, CitationType, WorkReport
from pub_analyzer.models.work import Work
from pub_analyzer.widgets.report.source import SourcesTable
from pub_analyzer.widgets.report.work import CitedByTable, WorksTable
from tests.data.builders import make_author_report, make_report_source, make_work
from tests.widgets.helpers import WidgetApp

LARGE_TABLE_ROWS = 500
"""Enough rows for a single render of a table to take a few tenths of a second."""

LARGE_REPORT_ROWS = 3000
"""Works in the largest reports in use, whose works table took seconds to show before it had pages."""

PAGINATED_RENDER_BUDGET = 1.0
"""Seconds a paginated table may spend rendering when shown, or when the terminal is resized."""


def make_work_with_doi(idx: int) -> Work:
    """Build a work with a DOI, which the tables show as a link."""
    return make_work(
        f"W{idx}",
        title=f"A long enough title to wrap across lines in the table, number {idx}",
        ids={"openalex": f"https://openalex.org/W{idx}", "doi": f"https://doi.org/10.1234/{idx}"},
        publication_date="2020-01-01",
    )


def make_works_table(rows: int) -> Widget:
    """Build a works table for an author report with many works."""
    report = make_author_report()
    report.works = [WorkReport(work=make_work_with_doi(idx), cited_by=[], citation_summary=CitationSummary()) for idx in range(rows)]
    return WorksTable(report)


def make_cited_by_table(rows: int) -> Widget:
    """Build the table of works citing a highly cited work."""
    return CitedByTable([CitationReport(work=make_work_with_doi(idx), citation_type=CitationType.TypeA) for idx in range(rows)])


def make_sources_table(rows: int) -> Widget:
    """Build the sources table for an author published in many sources."""
    return SourcesTable([make_report_source(f"S{idx}", f"Source {idx}") for idx in range(rows)])


class TableRenderTimer:
    """Record how long Rich spends rendering each table, from the moment it is created."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.renders: list[tuple[int, float]] = []
        """Rows and seconds of each render."""
        render = Table.__rich_console__

        def timed_render(table: Table, console: Console, options: ConsoleOptions) -> RenderResult:
            start = time.perf_counter()
            try:
                yield from render(table, console, options)
            finally:
                # Textual may stop reading once it has the lines it needs.
                self.renders.append((table.row_count, time.perf_counter() - start))

        monkeypatch.setattr(Table, "__rich_console__", timed_render)

    @property
    def total_time(self) -> float:
        """Seconds spent rendering tables."""
        return sum(duration for _, duration in self.renders)

    def summary(self) -> str:
        """Describe the renders, to explain a failed assertion."""
        rows = max((rows for rows, _ in self.renders), default=0)
        return f"rendered tables {len(self.renders)} times, with up to {rows} rows, taking {self.total_time:.2f}s"

    def reset(self) -> None:
        """Forget the renders recorded so far."""
        self.renders.clear()


def visible_links(pilot: Pilot, table: Widget) -> list[tuple[int, int]]:
    """Return a screen offset for each link of a table that is on screen.

    The tables are Rich tables rendered as text, so their links are not widgets. Look for
    the screen cells that carry a click action instead.
    """
    region = table.region.intersection(pilot.app.screen.region)
    links: dict[str, tuple[int, int]] = {}

    for y in range(region.y, region.bottom):
        for x in range(region.x, region.right):
            style = pilot.app.screen.get_style_at(x, y)
            if style.meta.get("@click"):
                links.setdefault(style.link_id, (x, y))

    return list(links.values())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_table",
    [
        pytest.param(make_works_table, id="works"),
        pytest.param(make_cited_by_table, id="cited-by"),
        pytest.param(make_sources_table, id="sources"),
    ],
)
async def test_hovering_links_does_not_render_the_table_again(
    make_table: Callable[[int], Widget],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Moving the mouse across a table's links spends no time rendering the table.

    Each table is a single Rich renderable, so rendering it takes time in proportion to the
    number of rows. Textual renders a widget again each time the mouse enters or leaves one
    of its links, to highlight it, which made large reports stall as the mouse moved.
    """
    table = make_table(LARGE_TABLE_ROWS)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        await pilot.pause()
        links = visible_links(pilot, table)
        assert len(links) >= 10, "The table shows too few links to hover over"

        timer = TableRenderTimer(monkeypatch)
        for offset in links[:10]:
            await pilot.hover(offset=offset)
        await pilot.hover("#focus-target")
        await pilot.pause()

    assert not timer.renders, f"Hovering over 10 links {timer.summary()}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_table",
    [
        pytest.param(make_works_table, id="works"),
        pytest.param(make_sources_table, id="sources"),
    ],
)
async def test_large_table_renders_one_page_of_rows(
    make_table: Callable[[int], Widget],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A table with thousands of rows shows quickly, and keeps up with the terminal being resized.

    Only one page of rows is rendered. Before the tables had pages, showing 3000 works took
    around 11 seconds, and each resize around 8 more.
    """
    table = make_table(LARGE_REPORT_ROWS)
    app = WidgetApp(table)
    timer = TableRenderTimer(monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        await pilot.pause()
        assert timer.total_time < PAGINATED_RENDER_BUDGET, f"Showing {LARGE_REPORT_ROWS} rows {timer.summary()}"

        timer.reset()
        await pilot.resize_terminal(120, 60)
        await pilot.pause()
        assert timer.total_time < PAGINATED_RENDER_BUDGET, f"Resizing the terminal {timer.summary()}"
