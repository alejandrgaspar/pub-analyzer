"""Searchbar widget."""

from enum import Enum

import httpx
from pydantic import TypeAdapter
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static

from pub_analyzer.models.author import AuthorResult
from pub_analyzer.models.institution import InstitutionResult
from pub_analyzer.widgets.common import Input, Select

from .results import AuthorResultWidget, InstitutionResultWidget


class SearchBar(Input):
    """SearchBar."""


class FinderWidget(Static):
    """Search in Open Alex API as-you-type Widget."""

    class OpenAlexEndPoint(Enum):
        """OpenAlex Endpoints."""

        AUTHOR = "https://api.openalex.org/autocomplete/authors?author_hint=institution"
        INSTITUTION = "https://api.openalex.org/autocomplete/institutions?"

    class EntityTypeSelector(Select[OpenAlexEndPoint]):
        """Entity_type Selector."""

    def __init__(self, url: OpenAlexEndPoint = OpenAlexEndPoint.AUTHOR) -> None:
        self.url = url
        super().__init__()

    def compose(self) -> ComposeResult:
        """Generate an input field and displays the results."""
        entity_options = [(name.title(), endpoint) for name, endpoint in self.OpenAlexEndPoint.__members__.items()]

        with Horizontal(classes="searchbar-container"):
            yield SearchBar(placeholder="Search author")
            yield self.EntityTypeSelector(options=entity_options, value=self.OpenAlexEndPoint.AUTHOR, allow_blank=False)
        yield VerticalScroll(id="results-container")

    async def lookup(self, input: str) -> None:
        """Search in OpenAlex API."""
        async with httpx.AsyncClient() as client:
            url = self.url.value + f"&q={input}"
            response = (await client.get(url)).json().get("results")

        if input == self.query_one(Input).value:
            # Clear the results
            await self.query("#results-container > *").remove()

            match self.url:
                case self.OpenAlexEndPoint.AUTHOR:
                    author_results: list[AuthorResult] = TypeAdapter(list[AuthorResult]).validate_python(response)
                    for author_result in author_results:
                        await self.query_one("#results-container").mount(AuthorResultWidget(author_result))
                    return

                case self.OpenAlexEndPoint.INSTITUTION:
                    institution_results: list[InstitutionResult] = TypeAdapter(list[InstitutionResult]).validate_python(response)
                    for institution_result in institution_results:
                        await self.query_one("#results-container").mount(InstitutionResultWidget(institution_result))
                    return

    @on(Input.Changed)
    async def on_type(self, event: Input.Changed) -> None:
        """Coroutine to handle search input."""
        if event.value:
            # Look up the author in the background
            self.run_worker(self.lookup(event.value), exclusive=True)
        else:
            # Clear the results
            await self.query("#results-container > *").remove()

    @on(Select.Changed)
    async def on_select_entity(self, event: Select.Changed) -> None:
        """Change entity endpoint."""
        search_bar = self.query_one(SearchBar)
        match event.value:
            case self.OpenAlexEndPoint.AUTHOR:
                self.url = self.OpenAlexEndPoint.AUTHOR
                search_bar.placeholder = "Search author"
            case self.OpenAlexEndPoint.INSTITUTION:
                self.url = self.OpenAlexEndPoint.INSTITUTION
                search_bar.placeholder = "Search institution"
            case _:
                self.url = self.OpenAlexEndPoint.AUTHOR
                search_bar.placeholder = "Search author"

        search_bar.value = ""
