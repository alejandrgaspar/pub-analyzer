"""Author Cards Widgets."""

from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from pub_analyzer.models.author import Author
from pub_analyzer.widgets.common import Card


class CitationMetricsCard(Card):
    """Citation metrics for this author."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Citation metrics:[/italic]", classes="card-title")

        with Vertical(classes="card-container"):
            yield Label(f"[bold]2-year mean:[/bold] {self.author.summary_stats.two_yr_mean_citedness:.5f}")
            yield Label(f"[bold]h-index:[/bold] {self.author.summary_stats.h_index}")
            yield Label(f"[bold]i10 index:[/bold] {self.author.summary_stats.i10_index}")


class IdentifiersCard(Card):
    """Card with external identifiers that we know about for this author."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Identifiers:[/italic]", classes="card-title")

        for platform, platform_url in self.author.ids.model_dump().items():
            if platform_url:
                yield Label(f"""- [@click=app.open_link('{quote(str(platform_url))}')]{platform}[/]""")


class LastInstitutionCard(Card):
    """Card with author's last known institutional affiliation."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Last Institution:[/italic]", classes="card-title")

        if self.author.last_known_institution:
            ror = self.author.last_known_institution.ror
            institution_name = self.author.last_known_institution.display_name

            with Vertical(classes="card-container"):
                yield Label(f"""[bold]Name:[/bold] [@click=app.open_link('{quote(str(ror))}')]{institution_name}[/]""")
                yield Label(f"[bold]Country:[/bold] {self.author.last_known_institution.country_code}")
                yield Label(f"[bold]Type:[/bold] {self.author.last_known_institution.type.value}")
