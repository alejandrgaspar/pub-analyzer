"""Module that allows searching for researchers using OpenAlex."""

import httpx
from pydantic import TypeAdapter
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Static

from pub_analyzer.models.researcher import ResearcherInfo
from pub_analyzer.widgets.researcher import ResearcherInfoWidget


class ResearcherResult(Static):
    """Researcher info widget."""

    def __init__(self, researcher_info: ResearcherInfo) -> None:
        self.researcher_info = researcher_info
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose researcher info widget."""
        yield Button(label=self.researcher_info.display_name)
        with Vertical(classes="vertical-content"):
            # Main info
            with Horizontal(classes="main-info-container"):
                yield Static(f'[bold]Cited by count:[/bold] {self.researcher_info.cited_by_count}')
                yield Static(f'[bold]Works count:[/bold] {self.researcher_info.works_count}')
                yield Static(f"""[@click="app.open_link('{self.researcher_info.external_id}')"]ORCID[/]""")

            # Author's hint
            yield Static(self.researcher_info.hint or "", classes="researcher-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Go to the researcher information page."""
        researcher_info_widget = ResearcherInfoWidget(researcher_info=self.researcher_info)

        self.app.query_one("#page-title", Static).update(self.researcher_info.display_name)
        self.app.query_one("MainContent").mount(researcher_info_widget)
        self.app.query_one("ResearcherFinder").remove()


class ResearcherFinder(Static):
    """Searches in Open Alex API as-you-type."""

    def compose(self) -> ComposeResult:
        """Generate an input field and displays the results."""
        yield Input(placeholder="Search for an researcher by name")
        yield VerticalScroll(id="results-container")

    async def on_input_changed(self, message: Input.Changed) -> None:
        """Coroutine to handle a text changed message."""
        if message.value:
            # Look up the researcher in the background
            self.run_worker(self.lookup_researcher(message.value), exclusive=True)
        else:
            # Clear the results
            await self.query("ResearcherResult").remove()

    async def lookup_researcher(self, name: str) -> None:
        """Use the OpenAlex api we look for the name entered by the user in the search box."""
        url = f"https://api.openalex.org/autocomplete/authors?q={name}&author_hint=institution"
        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json().get("results")

        if name == self.query_one(Input).value:
            # Clear the results
            await self.query("ResearcherResult").remove()

            researchers_info: list[ResearcherInfo] = TypeAdapter(list[ResearcherInfo]).validate_python(results)
            for researcher_info in researchers_info:
                await self.query_one("#results-container").mount(ResearcherResult(researcher_info=researcher_info))
