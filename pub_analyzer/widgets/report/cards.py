"""Report Cards Widgets."""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label

from pub_analyzer.models.report import Report
from pub_analyzer.widgets.common import Card


class ReportCitationMetricsCard(Card):
    """Citation metrics for this report."""

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label('[italic]Citation metrics:[/italic]', classes="card-title")

        with Vertical(classes='card-container'):
            yield Label(f'[bold]Count:[/bold] {self.report.author.cited_by_count}')
            yield Label(f'[bold]Type A:[/bold] {self.report.citation_resume.type_a_count}')
            yield Label(f'[bold]Type B:[/bold] {self.report.citation_resume.type_b_count}')


class WorksTypeResumeCard(Card):
    """Works Type Counters Resume Card."""

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label('[italic]Work Type[/italic]', classes='card-title')

        with VerticalScroll(classes='card-container'):
            for work_type_counter in self.report.works_type_resume:
                yield Label(f'[bold]{work_type_counter.type_name}:[/bold] {work_type_counter.count}')


class OpenAccessResumeCard(Card):
    """Open Access counts for this report."""

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose card."""
        yield Label('[italic]Open Access[/italic]', classes='card-title')

        with VerticalScroll(classes='card-container'):
            for status, count in self.report.open_access_resume.model_dump().items():
                yield Label(f'[bold]{status}:[/bold] {count}')
