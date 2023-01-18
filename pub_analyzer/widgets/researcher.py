"""Module that allows searching for researchers using OpenAlex."""

import asyncio

import httpx
from pydantic import BaseModel, parse_obj_as, validator
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static


class ResearcherInfo(BaseModel):
    """Information DictType from a researcher resulting from a search in OpenAlex."""

    id: str
    display_name: str
    hint: str | None = ""
    cited_by_count: int
    works_count: int
    entity_type: str
    external_id: str | None = ""

    class Config:
        """Allowing a value to be assigned during validation."""

        validate_assignment = True

    @validator("hint", "external_id")
    def set_default(cls, value: str) -> str:
        """Defining a default text."""
        return value or ""


class ResearcherResult(Static):
    """Researcher info widget."""

    def __init__(self, researcher_info: ResearcherInfo) -> None:
        self.researcher_info = researcher_info
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose researcher info widget."""
        yield Static(self.researcher_info.display_name, classes="researcher-name-container")
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


class ResearcherFinder(Static):
    """Searches in Open Alex API as-you-type."""

    def compose(self) -> ComposeResult:
        """Generates an input field and displays the results."""
        yield Input(placeholder="Search for an investigator by name")
        yield Vertical(Static(id="results"), id="results-container")

    async def on_input_changed(self, message: Input.Changed) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            # Look up the researcher in the background
            asyncio.create_task(self.lookup_researcher(message.value))
        else:
            # Clear the results
            await self.query("ResearcherResult").remove()

    async def lookup_researcher(self, name: str) -> None:
        """Looks up a word."""
        url = f"https://api.openalex.org/autocomplete/authors?q={name}"
        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json().get("results")

        if name == self.query_one(Input).value:
            # Clear the results
            await self.query("ResearcherResult").remove()

            researchers_info = parse_obj_as(list[ResearcherInfo], results)
            for researcher_info in researchers_info:
                await self.query_one("#results").mount(ResearcherResult(researcher_info=researcher_info))
