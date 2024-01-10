"""Module with Widgets that allows to display the complete information of Institution using OpenAlex."""

from typing import Any

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Collapsible, Label, Static

from pub_analyzer.internal.identifier import get_institution_id
from pub_analyzer.models.institution import Institution, InstitutionResult
from pub_analyzer.widgets.common.filters import DateRangeFilter, Filter
from pub_analyzer.widgets.common.summary import SummaryWidget
from pub_analyzer.widgets.report.core import CreateInstitutionReportWidget

from .cards import CitationMetricsCard, IdentifiersCard, RolesCard
from .tables import InstitutionWorksByYearTable


class _InstitutionSummaryWidget(Static):
    """Institution info summary."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose institution info."""
        is_report_not_available = self.institution.works_count < 1

        # Compose Cards
        with Vertical(classes="block-container"):
            yield Label("[bold]Institution info:[/bold]", classes="block-title")

            with Horizontal(classes="cards-container"):
                yield RolesCard(institution=self.institution)
                yield IdentifiersCard(institution=self.institution)
                yield CitationMetricsCard(institution=self.institution)

        # Work realeted info
        with Vertical(classes="block-container"):
            yield Label("[bold]Work Info:[/bold]", classes="block-title")

            with Horizontal(classes="info-container"):
                yield Label(f"[bold]Cited by count:[/bold] {self.institution.cited_by_count}")
                yield Label(f"[bold]Works count:[/bold] {self.institution.works_count}")

        # Count by year table section
        with Container(classes="table-container"):
            yield InstitutionWorksByYearTable(institution=self.institution)

        # Make report section
        with Vertical(classes="block-container", disabled=is_report_not_available):
            yield Label("[bold]Make report:[/bold]", classes="block-title")

            # Filters
            with Collapsible(title="Report filters.", classes="filter-collapsible"):
                # Institution publication Date Range
                yield DateRangeFilter(checkbox_label="Publication date range:", id="institution-date-range-filter")

                # Cite Date Range
                yield DateRangeFilter(checkbox_label="Cited date range:", id="cited-date-range-filter")

            # Button
            with Vertical(classes="block-container button-container"):
                yield Button("Make Report", variant="primary", id="make-report-button")


class InstitutionSummaryWidget(SummaryWidget):
    """Institution info summary container."""

    def __init__(self, institution_result: InstitutionResult) -> None:
        self.institution_result = institution_result
        self.institution: Institution
        super().__init__()

    def on_mount(self) -> None:
        """Hide the empty container and call data in the background."""
        self.loading = True
        self.run_worker(self.load_data(), exclusive=True)

    async def _get_info(self) -> None:
        """Query OpenAlex API."""
        institution_id = get_institution_id(self.institution_result)
        url = f"https://api.openalex.org/institutions/{institution_id}"

        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json()
            self.institution = Institution(**results)

    async def load_data(self) -> None:
        """Query OpenAlex API and composing the widget."""
        await self._get_info()
        await self.mount(_InstitutionSummaryWidget(institution=self.institution))

        self.loading = False

    @on(Filter.Changed)
    def filter_change(self) -> None:
        """Handle filter changes."""
        filters = [filter for filter in self.query("_InstitutionSummaryWidget Filter").results(Filter) if not filter.filter_disabled]
        all_filters_valid = all(filter.validation_state for filter in filters)

        self.query_one("_InstitutionSummaryWidget #make-report-button", Button).disabled = not all_filters_valid

    @on(Button.Pressed, "#make-report-button")
    async def make_report(self) -> None:
        """Make the author report."""
        filters: dict[str, Any] = {}
        pub_date_range = self.query_one("#institution-date-range-filter", DateRangeFilter)
        cited_date_range = self.query_one("#cited-date-range-filter", DateRangeFilter)

        if not pub_date_range.filter_disabled:
            filters.update({"pub_from_date": pub_date_range.from_date, "pub_to_date": pub_date_range.to_date})

        if not cited_date_range.filter_disabled:
            filters.update({"cited_from_date": cited_date_range.from_date, "cited_to_date": cited_date_range.to_date})

        report_widget = CreateInstitutionReportWidget(institution=self.institution, **filters)
        await self.app.query_one("MainContent").mount(report_widget)
        await self.app.query_one("InstitutionSummaryWidget").remove()
