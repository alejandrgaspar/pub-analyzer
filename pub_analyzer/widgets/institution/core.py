"""Module with Widgets that allows to display the complete information of Institution using OpenAlex."""

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, LoadingIndicator, Static

from pub_analyzer.internal.identifier import get_institution_id
from pub_analyzer.models.institution import Institution, InstitutionResult
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

    @on(Button.Pressed, "#make-report-button")
    async def make_report(self) -> None:
        """Make the institution report."""
        report_widget = CreateInstitutionReportWidget(institution=self.institution, works_api_url=self.institution.works_api_url)

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
                Button("Make Report", variant="primary", id="make-report-button", disabled=is_report_not_available),
                classes="block-container button-container"
            )
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True