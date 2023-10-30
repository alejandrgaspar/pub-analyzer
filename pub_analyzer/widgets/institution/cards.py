"""Institution Cards Widgets."""

from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from pub_analyzer.models.institution import Institution
from pub_analyzer.widgets.common import Card


class CitationMetricsCard(Card):
    """Citation metrics for this institution."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Citation metrics:[/italic]", classes="card-title")

        with Vertical(classes="card-container"):
            yield Label(f"[bold]2-year mean:[/bold] {self.institution.summary_stats.two_yr_mean_citedness:.5f}")
            yield Label(f"[bold]h-index:[/bold] {self.institution.summary_stats.h_index}")
            yield Label(f"[bold]i10 index:[/bold] {self.institution.summary_stats.i10_index}")


class IdentifiersCard(Card):
    """Card with external identifiers that we know about this institution."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Identifiers:[/italic]", classes="card-title")

        for platform, platform_url in self.institution.ids.model_dump().items():
            if platform_url:
                yield Label(f"""- [@click=app.open_link('{quote(str(platform_url))}')]{platform}[/]""")

        if self.institution.homepage_url:
            yield Label(f"""- [@click=app.open_link('{quote(str(self.institution.homepage_url))}')]Homepage[/]""")


class GeoCard(Card):
    """Card with location info of this institution."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Geo:[/italic]", classes="card-title")

        with Vertical(classes="card-container"):
            yield Label(f"[bold]City:[/bold] {self.institution.geo.city}")
            yield Label(f"[bold]Country:[/bold] {self.institution.geo.country}")


class RolesCard(Card):
    """Card with roles info of this institution."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Works by roles:[/italic]", classes="card-title")

        with Vertical(classes="card-container"):
            for role in self.institution.roles:
                yield Label(f"""[@click=app.open_link('{quote(str(role.id))}')]{role.role.value.title()}[/]: {role.works_count}""")
