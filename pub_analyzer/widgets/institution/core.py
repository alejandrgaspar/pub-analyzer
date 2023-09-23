"""Module with Widgets that allows to display the complete information of Institution using OpenAlex."""

import datetime

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Label, LoadingIndicator, Static

from pub_analyzer.internal.identifier import get_institution_id
from pub_analyzer.models.institution import Institution, InstitutionResult
from pub_analyzer.widgets.common import DateInput
from pub_analyzer.widgets.report.core import CreateInstitutionReportWidget

from .cards import CitationMetricsCard, IdentifiersCard, RolesCard
from .tables import InstitutionWorksByYearTable


class InstitutionResumeWidget(Static):
    """Institution info resume."""

    def __init__(self, institution_result: InstitutionResult) -> None:
        self.institution_result = institution_result
        self.institution: Institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        yield LoadingIndicator()
        yield VerticalScroll(id="main-container")

    def on_mount(self) -> None:
        """Hiding the empty container and calling the data in the background."""
        self.query_one("#main-container", VerticalScroll).display = False
        self.run_worker(self.load_data(), exclusive=True)

    @on(Checkbox.Changed, "#filters-checkbox")
    async def toggle_filter(self, event: Checkbox.Changed) -> None:
        """Toggle filters."""
        if event.checkbox.value:
            for date_input in self.query(DateInput).results(DateInput):
                date_input.disabled = False
                date_input.value = ""
        else:
            for date_input in self.query(DateInput).results(DateInput):
                date_input.disabled = True
                date_input.value = ""
                self.query_one("#make-report-button", Button).disabled = False

    @on(DateInput.Changed)
    async def enable_make_report(self, event: DateInput.Changed) -> None:
        """Enable make report button."""
        checkbox = self.query_one("#filters-checkbox", Checkbox)

        if event.validation_result:
            if not event.validation_result.is_valid and checkbox.value:
                self.query_one("#make-report-button", Button).disabled = True
            else:
                self.query_one("#make-report-button", Button).disabled = False

    @on(Button.Pressed, "#make-report-button")
    async def make_report(self) -> None:
        """Make the institution report."""
        checkbox = self.query_one("#filters-checkbox", Checkbox)
        from_input = self.query_one("#from-date", DateInput)
        to_input = self.query_one("#to-date", DateInput)

        if checkbox.value and (from_input.value or to_input.value):
            date_format = "%Y-%m-%d"
            from_date = datetime.datetime.strptime(from_input.value, date_format) if from_input.value else None
            to_date = datetime.datetime.strptime(to_input.value, date_format) if to_input.value else None

            report_widget = CreateInstitutionReportWidget(institution=self.institution, from_date=from_date, to_date=to_date)
        else:
            report_widget = CreateInstitutionReportWidget(institution=self.institution)

        await self.app.query_one("MainContent").mount(report_widget)
        await self.app.query_one("InstitutionResumeWidget").remove()

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
        container = self.query_one("#main-container", VerticalScroll)
        is_report_not_available = self.institution.works_count < 1

        # Compose Cards
        await container.mount(
            Vertical(
                Label('[bold]Institution info:[/bold]', classes="block-title"),
                Horizontal(
                    RolesCard(institution=self.institution),
                    IdentifiersCard(institution=self.institution),
                    CitationMetricsCard(institution=self.institution),
                    classes="cards-container"
                ),
                classes="block-container"
            )
        )

        # Work realeted info
        await container.mount(
            Vertical(
                Label('[bold]Work Info:[/bold]', classes="block-title"),
                Horizontal(
                    Label(f'[bold]Cited by count:[/bold] {self.institution.cited_by_count}'),
                    Label(f'[bold]Works count:[/bold] {self.institution.works_count}'),
                    classes="info-container"
                ),
                classes="block-container"
            )
        )

        # Count by year table section
        await container.mount(
            Container(
                InstitutionWorksByYearTable(institution=self.institution),
                classes="table-container"
            )
        )

        # Report Button
        await container.mount(
            Vertical(
                Label('[bold]Make report:[/bold]', classes="block-title"),

                # Filters
                Horizontal(
                    Checkbox("Filter", id="filters-checkbox"),
                    DateInput(placeholder="From yyyy-mm-dd", disabled=True, id="from-date"),
                    DateInput(placeholder="To yyyy-mm-dd", disabled=True, id="to-date"),
                    classes="info-container filter-container",
                ),

                # Button
                Vertical(
                    Button("Make Report", variant="primary", id="make-report-button"),
                    classes="block-container button-container"
                ),
                classes="block-container",
                disabled=is_report_not_available
            )
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True
