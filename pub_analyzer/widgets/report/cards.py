"""Report Cards Widgets."""

from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import AuthorReport, InstitutionReport, WorkReport
from pub_analyzer.models.work import Work
from pub_analyzer.widgets.common import Card


# Works pane cards.
class ReportCitationMetricsCard(Card):
    """Citation metrics for this report."""

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Citation metrics:[/italic]", classes="card-title")

        with Vertical(classes="card-container"):
            type_a_count = self.report.citation_summary.type_a_count
            type_b_count = self.report.citation_summary.type_b_count
            cited_by_count = type_a_count + type_b_count

            yield Label(f"[bold]Count:[/bold] {cited_by_count}")
            yield Label(f"[bold]Type A:[/bold] {type_a_count}")
            yield Label(f"[bold]Type B:[/bold] {type_b_count}")


class WorksTypeSummaryCard(Card):
    """Works Type Counters Summary Card."""

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Work Type[/italic]", classes="card-title")

        with VerticalScroll(classes="card-container"):
            for work_type_counter in self.report.works_type_summary:
                yield Label(f"[bold]{work_type_counter.type_name}:[/bold] {work_type_counter.count}")


class OpenAccessSummaryCard(Card):
    """Open Access counts for this report."""

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Open Access[/italic]", classes="card-title")

        with VerticalScroll(classes="card-container"):
            for status, count in self.report.open_access_summary.model_dump().items():
                yield Label(f"[bold]{status.capitalize()}:[/bold] {count}")


# Work Info cards.
class AuthorshipCard(Card):
    """Card that enumerate the authorship's of a work."""

    def __init__(self, work: Work, author: Author | None) -> None:
        self.work = work
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label("[italic]Authorship's[/italic]", classes="card-title")

        with VerticalScroll(classes="card-container"):
            for authorship in self.work.authorships:
                # If the author was provided, highlight
                if self.author and authorship.author.display_name == self.author.display_name:
                    author_name_formated = f"[b #909d63]{authorship.author.display_name}[/]"
                else:
                    author_name_formated = str(authorship.author.display_name)

                external_id = authorship.author.orcid or authorship.author.id
                yield Label(
                    f"""- [b]{authorship.author_position}:[/b] [@click=app.open_link('{quote(str(external_id))}')]{author_name_formated}[/]"""  # noqa: E501
                )


class OpenAccessCard(Card):
    """Card that show OpenAccess status of a work."""

    def __init__(self, work: Work) -> None:
        self.work = work
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        work_url = self.work.open_access.oa_url

        yield Label("[italic]Open Access[/italic]", classes="card-title")
        yield Label(f"[bold]Status:[/bold] {self.work.open_access.oa_status.value.capitalize()}")
        if work_url:
            yield Label(f"""[bold]URL:[/bold] [@click=app.open_link('{quote(str(work_url))}')]{work_url}[/]""")


class CitationMetricsCard(Card):
    """Card that show Citation metrics of a work."""

    def __init__(self, work_report: WorkReport) -> None:
        self.work_report = work_report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        type_a_count = self.work_report.citation_summary.type_a_count
        type_b_count = self.work_report.citation_summary.type_b_count
        cited_by_count = type_a_count + type_b_count

        yield Label("[italic]Citation[/italic]", classes="card-title")

        yield Label(f"[bold]Count:[/bold] {cited_by_count}")
        yield Label(f"[bold]Type A:[/bold] {type_a_count}")
        yield Label(f"[bold]Type B:[/bold] {type_b_count}")
