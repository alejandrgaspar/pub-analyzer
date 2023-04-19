"""Researcher info module."""

from urllib.parse import urlparse

import httpx
from rich.table import Table
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from pub_analyzer.models.researcher import ResearcherExtendedInfo, ResearcherInfo


class ResearcherInfoWidget(Static):
    """Extended info of researcher."""

    def __init__(self, researcher_info: ResearcherInfo) -> None:
        self.researcher_info = researcher_info
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create info container of researcher."""
        yield Vertical(
            Static('[bold]Work Info:[/bold]', classes="info-block-title"),
            Horizontal(
                Static(f'[bold]Cited by count:[/bold] {self.researcher_info.cited_by_count}'),
                Static(f'[bold]Works count:[/bold] {self.researcher_info.works_count}'),
                classes="info-container"
            ),
            classes="researcher-block-container"
        )

        yield Vertical(
            Static('[bold]Extended Info:[/bold]', classes="info-block-title"),
            Container(id="extended-info-container"),
            classes="researcher-block-container"
        )

    async def refresh_researcher_info(self) -> None:
        """Get extended info from OpenAlex to render the rest of the information."""
        author_id = urlparse(self.researcher_info.id).path.rpartition('/')[2]
        url = f"https://api.openalex.org/authors/{author_id}"

        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json()
            researcher_info = ResearcherExtendedInfo(**results)

        container = self.app.query_one("#extended-info-container")

        # Last institution
        if researcher_info.last_known_institution:
            ror = researcher_info.last_known_institution.ror
            institution_name = researcher_info.last_known_institution.display_name

            await container.mount(
                Vertical(
                    Static('[italic]Last Institution:[/italic]', classes="info-block-title"),

                    Static(f'''[bold]Name:[/bold] [@click="app.open_link('{ror}')"]{institution_name}[/]'''),
                    Static(f'[bold]Country:[/bold] {researcher_info.last_known_institution.country_code}'),
                    Static(f'[bold]Type:[/bold] {researcher_info.last_known_institution.type}'),
                    classes="grid-box",
                )
            )
        else:
            await container.mount(
                Vertical(
                    Static('[italic]Last Institution:[/italic]', classes="info-block-title"),
                    classes="grid-box",
                )
            )

        # External links
        await container.mount(
            Vertical(
                Static('[italic]External Links:[/italic]', classes="info-block-title"),

                *[
                    Static(f"""- [@click="app.open_link('{platform_url}')"]{platform}[/]""")
                    for platform, platform_url in researcher_info.ids.dict().items() if platform_url
                ],
                classes="grid-box"
            )
        )

        # Citation metrics
        await container.mount(
            Vertical(
                Static('[italic]Citation metrics:[/italic]', classes="info-block-title"),

                Static(f'[bold]2-year mean:[/bold] {researcher_info.summary_stats.two_yr_mean_citedness:.5f}'),
                Static(f'[bold]h-index:[/bold] {researcher_info.summary_stats.h_index}'),
                Static(f'[bold]i10 index:[/bold] {researcher_info.summary_stats.i10_index}'),

                classes="grid-box"
            )
        )

        # Count by year table section
        table = Table('Year', 'Works Count', 'Cited by Count', title="Counts by Year", expand=True)
        for row in researcher_info.counts_by_year:
            year, works_count, cited_by_count = row.dict().values()
            table.add_row(str(year), str(works_count), str(cited_by_count))

        await container.mount(
            Container(
                Static(table),
                classes="grid-box grid-size-3"
            )
        )

    def on_mount(self) -> None:
        """Set things in motion on mount."""
        self.call_after_refresh(self.refresh_researcher_info)
