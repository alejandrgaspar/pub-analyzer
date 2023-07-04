"""Module with Widgets that allows to display the complete information of an Author using OpenAlex."""

import httpx
from rich.table import Table
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, LoadingIndicator, Static

from pub_analyzer.models.author import Author, AuthorResult
from pub_analyzer.utils.identifier import get_author_id
from pub_analyzer.widgets.report.core import ReportWidget


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
        report_widget = ReportWidget(author=self.author, works_api_url=self.author.works_api_url)

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

        # Last institution
        if self.author.last_known_institution:
            ror = self.author.last_known_institution.ror
            institution_name = self.author.last_known_institution.display_name
            institution_card = Vertical(
                Label('[italic]Last Institution:[/italic]', classes="card-title"),

                Label(f'''[bold]Name:[/bold] [@click="app.open_link('{ror}')"]{institution_name}[/]'''),
                Label(f'[bold]Country:[/bold] {self.author.last_known_institution.country_code}'),
                Label(f'[bold]Type:[/bold] {self.author.last_known_institution.type}'),
                classes="card",
            )
        else:
            institution_card = Vertical(
                Label('[italic]Last Institution:[/italic]', classes="block-title"),
                classes="card",
            )

        # External links
        links_card = Vertical(
            Label('[italic]External Links:[/italic]', classes="card-title"),

            *[
                Label(f"""- [@click="app.open_link('{platform_url}')"]{platform}[/]""")
                for platform, platform_url in self.author.ids.model_dump().items() if platform_url
            ],
            classes="card"
        )

        # Citation metrics
        metrics_card = Vertical(
            Label('[italic]Citation metrics:[/italic]', classes="card-title"),

            Label(f'[bold]2-year mean:[/bold] {self.author.summary_stats.two_yr_mean_citedness:.5f}'),
            Label(f'[bold]h-index:[/bold] {self.author.summary_stats.h_index}'),
            Label(f'[bold]i10 index:[/bold] {self.author.summary_stats.i10_index}'),

            classes="card"
        )

        # Compose Cards
        await container.mount(
            Vertical(
                Label('[bold]Author info:[/bold]', classes="block-title"),
                Horizontal(
                    institution_card, links_card, metrics_card,
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
        table = Table('Year', 'Works Count', 'Cited by Count', title="Counts by Year", expand=True)
        for row in self.author.counts_by_year:
            year, works_count, cited_by_count = row.model_dump().values()
            table.add_row(str(year), str(works_count), str(cited_by_count))

        await container.mount(
            Container(
                Static(table),
                classes="table-container"
            )
        )

        # Report Button
        await container.mount(
            Vertical(
                Button("Make Report", variant="primary", id="make-report-button"),
                classes="block-container button-container"
            )
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True
