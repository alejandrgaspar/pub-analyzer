"""Module with Widgets that allows to display the complete information of an Author using OpenAlex."""

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, LoadingIndicator, Static

from pub_analyzer.internal.identifier import get_author_id
from pub_analyzer.models.author import Author, AuthorResult
from pub_analyzer.widgets.report.core import CreateAuthorReportWidget

from .cards import CitationMetricsCard, IdentifiersCard, LastInstitutionCard
from .tables import AuthorWorksByYearTable


class AuthorResumeWidget(Static):
    """Author info resume."""

    def __init__(self, author_result: AuthorResult) -> None:
        self.author_result = author_result
        self.author: Author
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
        """Make the author report."""
        report_widget = CreateAuthorReportWidget(author=self.author, works_api_url=self.author.works_api_url)

        await self.app.query_one("MainContent").mount(report_widget)
        await self.app.query_one("AuthorResumeWidget").remove()

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
        container = self.query_one("#main-container", VerticalScroll)
        is_report_not_available = self.author.works_count < 1

        # Compose Cards
        await container.mount(
            Vertical(
                Label('[bold]Author info:[/bold]', classes="block-title"),
                Horizontal(
                    LastInstitutionCard(author=self.author),
                    IdentifiersCard(author=self.author),
                    CitationMetricsCard(author=self.author),
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
                    Label(f'[bold]Cited by count:[/bold] {self.author.cited_by_count}'),
                    Label(f'[bold]Works count:[/bold] {self.author.works_count}'),
                    classes="info-container"
                ),
                classes="block-container"
            )
        )

        # Count by year table section
        await container.mount(
            Container(
                AuthorWorksByYearTable(author=self.author),
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
