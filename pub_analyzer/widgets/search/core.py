"""Searchbar widget."""

from enum import Enum

import httpx
from pydantic import TypeAdapter
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from pub_analyzer.models.author import AuthorResult
from pub_analyzer.widgets.common import Input

from .author import AuthorResultWidget


class SearchBar(Input):
    """SearchBar."""


class FinderWidget(Static):
    """Search in Open Alex API as-you-type Widget."""

    class EndPoint(Enum):
        """OpenAlex Endpoints."""

        AUTHOR = "https://api.openalex.org/autocomplete/authors?author_hint=institution"

    def __init__(self, url: EndPoint = EndPoint.AUTHOR) -> None:
        self.url = url
        super().__init__()

    def compose(self) -> ComposeResult:
        """Generate an input field and displays the results."""
        yield SearchBar(placeholder="Search for an author by name")
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
                case self.EndPoint.AUTHOR:
                    results: list[AuthorResult] = TypeAdapter(list[AuthorResult]).validate_python(response)
                    result_widget = AuthorResultWidget

            for result in results:
                await self.query_one("#results-container").mount(result_widget(result))

    @on(Input.Changed)
    async def on_type(self, event: Input.Changed) -> None:
        """Coroutine to handle search input."""
        if event.value:
            # Look up the author in the background
            self.run_worker(self.lookup(event.value), exclusive=True)
        else:
            # Clear the results
            await self.query("#results-container > *").remove()
