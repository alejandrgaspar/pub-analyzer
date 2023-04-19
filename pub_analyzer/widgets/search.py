"""Module that allows searching for researchers using OpenAlex."""

import asyncio

import httpx
from pydantic import parse_obj_as
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
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
        yield Vertical(
            Horizontal(
                Static(f'[bold]Cited by count:[/bold] {self.researcher_info.cited_by_count}'),
                Static(f'[bold]Works count:[/bold] {self.researcher_info.works_count}'),
                Static(f"""[@click="app.open_link('{self.researcher_info.external_id}')"]ORCID[/]"""),
                classes="main-info-container"
            ),
            Static(
                Text(self.researcher_info.hint, justify="full", overflow="ellipsis"), #type:ignore
                classes="researcher-hint"
            ),
            classes="vertical-content"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Go to the researcher information page."""
        page_title = self.app.query_one("#page-title", Static)
        page_title.renderable = self.researcher_info.display_name
        page_title.refresh()

        self.app.query_one("#main-content-container").mount(
            ResearcherInfoWidget(researcher_info=self.researcher_info)
        )
        self.app.query_one("ResearcherFinder").remove()


class ResearcherFinder(Static):
    """Searches in Open Alex API as-you-type."""

    def compose(self) -> ComposeResult:
        """Generate an input field and displays the results."""
        yield Input(placeholder="Search for an investigator by name")
        yield Vertical(Static(id="results"), id="results-container")

    async def on_input_changed(self, message: Input.Changed) -> None:
        """Coroutine to handle a text changed message."""
        if message.value:
            # Look up the researcher in the background
            asyncio.create_task(self.lookup_researcher(message.value))
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

            researchers_info = parse_obj_as(list[ResearcherInfo], results)
            for researcher_info in researchers_info:
                await self.query_one("#results").mount(ResearcherResult(researcher_info=researcher_info))
