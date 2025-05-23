"""Module that allows searching for authors using OpenAlex."""

from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, Static

from pub_analyzer.models.author import AuthorResult
from pub_analyzer.models.institution import InstitutionResult
from pub_analyzer.widgets.author.core import AuthorSummaryWidget
from pub_analyzer.widgets.institution.core import InstitutionSummaryWidget


class ResultWidget(Static):
    """Result Widget."""

    DEFAULT_CLASSES = "result-widget"


class AuthorResultWidget(ResultWidget):
    """Author result widget."""

    def __init__(self, author_result: AuthorResult) -> None:
        self.author_result = author_result
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Author result widget."""
        orcid_link = self.author_result.external_id

        yield Button(label=self.author_result.display_name)
        with Vertical(classes="vertical-content"):
            # Main info
            with Horizontal(classes="main-info-container"):
                yield Label(f"[bold]Cited by count:[/bold] {self.author_result.cited_by_count}", classes="cited-by-count")
                yield Label(f"[bold]Works count:[/bold] {self.author_result.works_count}", classes="works-count")

                if orcid_link:
                    yield Label(f"""[@click=app.open_link('{quote(str(orcid_link))}')]ORCID[/]""", classes="external-id")
                else:
                    yield Label(f"""[@click=app.open_link('{quote(str(self.author_result.id))}')]OpenAlexID[/]""", classes="external-id")

            # Author hint
            yield Label(self.author_result.hint or "", classes="text-hint")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Go to the Author summary page."""
        from pub_analyzer.widgets.body import MainContent

        author_summary_widget = AuthorSummaryWidget(author_result=self.author_result)
        self.post_message(MainContent.UpdateMainContent(new_widget=author_summary_widget, title=self.author_result.display_name))


class InstitutionResultWidget(ResultWidget):
    """Institution result widget."""

    def __init__(self, institution_result: InstitutionResult) -> None:
        self.institution_result = institution_result
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Institution result widget."""
        yield Button(label=self.institution_result.display_name)
        with Vertical(classes="vertical-content"):
            # Main info
            with Horizontal(classes="main-info-container"):
                external_id = self.institution_result.external_id or self.institution_result.id

                yield Label(f"[bold]Cited by count:[/bold] {self.institution_result.cited_by_count}", classes="cited-by-count")
                yield Label(f"[bold]Works count:[/bold] {self.institution_result.works_count}", classes="works-count")
                yield Label(f"""[@click=app.open_link('{quote(str(external_id))}')]External ID[/]""", classes="external-id")

            # Institution hint
            yield Label(self.institution_result.hint or "", classes="text-hint")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Go to the Institution summary page."""
        from pub_analyzer.widgets.body import MainContent

        institution_summary_widget = InstitutionSummaryWidget(institution_result=self.institution_result)
        self.post_message(MainContent.UpdateMainContent(new_widget=institution_summary_widget, title=self.institution_result.display_name))
