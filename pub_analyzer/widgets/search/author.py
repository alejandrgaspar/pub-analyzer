"""Module that allows searching for authors using OpenAlex."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, Static

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
        from pub_analyzer.widgets.body import MainContent
        author_resume_widget = AuthorResumeWidget(author_result=self.author_result)


        main_content = self.app.query_one(MainContent)
        main_content.update_title(title=self.author_result.display_name)
        await main_content.mount(author_resume_widget)

        await self.app.query_one("FinderWidget").remove()
