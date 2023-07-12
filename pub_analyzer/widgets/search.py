"""Module that allows searching for authors using OpenAlex."""

import httpx
from pydantic import TypeAdapter
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Input, Label, Static

from pub_analyzer.models.author import AuthorResult
from pub_analyzer.widgets.author.core import AuthorResumeWidget


class AuthorResultWidget(Static):
    """Author result widget."""

    def __init__(self, author_result: AuthorResult) -> None:
        self.author_result = author_result
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Author result widget."""
        yield Button(label=self.author_result.display_name)
        with Vertical(classes="vertical-content"):
            # Main info
            with Horizontal(classes="main-info-container"):
                yield Label(f'[bold]Cited by count:[/bold] {self.author_result.cited_by_count}', classes="cited-by-count")
                yield Label(f'[bold]Works count:[/bold] {self.author_result.works_count}', classes="works-count")
                yield Label(f"""[@click="app.open_link('{self.author_result.external_id}')"]ORCID[/]""", classes="external-id")

            # Author hint
            yield Label(self.author_result.hint or "", classes="author-hint")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Go to the Author resume page."""
        author_resume_widget = AuthorResumeWidget(author_result=self.author_result)

        self.app.query_one("#page-title", Static).update(self.author_result.display_name)
        await self.app.query_one("MainContent").mount(author_resume_widget)
        await self.app.query_one(AuthorFinderWidget).remove()


class AuthorSearchBar(Input):
    """SearchBar."""

    @on(Key)
    def exit_focus(self, message: Key) -> None:
        """Unfocus from the input with esc KEY."""
        if message.key == 'escape':
            self.screen.set_focus(None)


class AuthorFinderWidget(Static):
    """Searches Author in Open Alex API as-you-type."""

    def compose(self) -> ComposeResult:
        """Generate an input field and displays the results."""
        yield AuthorSearchBar(placeholder="Search for an author by name")
        yield VerticalScroll(id="results-container")

    async def on_input_changed(self, message: Input.Changed) -> None:
        """Coroutine to handle a text changed message."""
        if message.value:
            # Look up the author in the background
            self.run_worker(self.lookup_author(message.value), exclusive=True)
        else:
            # Clear the results
            await self.query(AuthorResultWidget).remove()

    async def lookup_author(self, name: str) -> None:
        """Use the OpenAlex api we look for the name entered by the user in the search box."""
        url = f"https://api.openalex.org/autocomplete/authors?q={name}&author_hint=institution"
        async with httpx.AsyncClient() as client:
            results = (await client.get(url)).json().get("results")

        if name == self.query_one(Input).value:
            # Clear the results
            await self.query(AuthorResultWidget).remove()

            authors_results: list[AuthorResult] = TypeAdapter(list[AuthorResult]).validate_python(results)
            for author_result in authors_results:
                await self.query_one("#results-container").mount(AuthorResultWidget(author_result=author_result))
