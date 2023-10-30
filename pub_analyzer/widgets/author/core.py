"""Module with Widgets that allows to display the complete information of an Author using OpenAlex."""

from typing import Any

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Collapsible, Label, Static

from pub_analyzer.internal.identifier import get_author_id
from pub_analyzer.models.author import Author, AuthorResult
from pub_analyzer.widgets.common.filters import DateRangeFilter, Filter
from pub_analyzer.widgets.report.core import CreateAuthorReportWidget

from .cards import CitationMetricsCard, IdentifiersCard, LastInstitutionCard
from .tables import AuthorWorksByYearTable


class _AuthorResumeWidget(Static):
    """Author info resume."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose author info."""
        is_report_not_available = self.author.works_count < 1

        # Compose Cards
        with Vertical(classes="block-container"):
            yield Label('[bold]Author info:[/bold]', classes="block-title")

            with Horizontal(classes="cards-container"):
                yield LastInstitutionCard(author=self.author)
                yield IdentifiersCard(author=self.author)
                yield CitationMetricsCard(author=self.author)

        # Work realeted info
        with Vertical(classes="block-container"):
            yield Label('[bold]Work Info:[/bold]', classes="block-title")

            with Horizontal(classes="info-container"):
                yield Label(f'[bold]Cited by count:[/bold] {self.author.cited_by_count}')
                yield Label(f'[bold]Works count:[/bold] {self.author.works_count}')

        # Count by year table section
        with Container(classes="table-container"):
            yield AuthorWorksByYearTable(author=self.author)

        # Make report section
        with Vertical(classes="block-container", disabled=is_report_not_available):
            yield Label('[bold]Make report:[/bold]', classes="block-title")

            # Filters
            with Collapsible(title="Report filters.", classes="filter-collapsible"):
                # Author publication Date Range
                yield DateRangeFilter(checkbox_label="Publication date range:", id="author-date-range-filter")

                # Cite Date Range
                yield DateRangeFilter(checkbox_label="Cited date range:", id="cited-date-range-filter")

            # Button
            with Vertical(classes="block-container button-container"):
                yield Button("Make Report", variant="primary", id="make-report-button")


class AuthorResumeWidget(VerticalScroll):
    """Author info resume container."""

    def __init__(self, author_result: AuthorResult) -> None:
        self.author_result = author_result
        self.author: Author
        super().__init__()

    def on_mount(self) -> None:
        """Hide the empty container and call data in the background."""
        self.loading = True
        self.run_worker(self.load_data(), exclusive=True)

    async def _get_info(self) -> None:
        """Query OpenAlex API."""
        author_id = get_author_id(self.author_result)
        url = f"https://api.openalex.org/authors/{author_id}"

        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json()
            self.author = Author(**results)

    async def load_data(self) -> None:
        """Query OpenAlex API and composing the widget."""
        await self._get_info()
        await self.mount(_AuthorResumeWidget(author=self.author))

        self.loading = False

    @on(Filter.Changed)
    def filter_change(self) -> None:
        """Handle filter changes."""
        filters = [filter for filter in self.query("_AuthorResumeWidget Filter").results(Filter) if not filter.filter_disabled]
        all_filters_valid = all(filter.validation_state for filter in filters)

        self.query_one("_AuthorResumeWidget #make-report-button", Button).disabled = not all_filters_valid

    @on(Button.Pressed, "#make-report-button")
    async def make_report(self) -> None:
        """Make the author report."""
        filters: dict[str, Any] = {}
        pub_date_range = self.query_one("#author-date-range-filter", DateRangeFilter)
        cited_date_range = self.query_one("#cited-date-range-filter", DateRangeFilter)

        if not pub_date_range.filter_disabled:
            filters.update({"pub_from_date": pub_date_range.from_date, "pub_to_date":pub_date_range.to_date})

        if not cited_date_range.filter_disabled:
            filters.update({"cited_from_date": cited_date_range.from_date, "cited_to_date":cited_date_range.to_date})

        report_widget = CreateAuthorReportWidget(author=self.author, **filters)
        await self.app.query_one("MainContent").mount(report_widget)
        await self.app.query_one("AuthorResumeWidget").remove()
