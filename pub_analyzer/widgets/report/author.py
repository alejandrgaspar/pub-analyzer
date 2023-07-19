"""Author Report Widgets."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll

from pub_analyzer.models.report import Report
from pub_analyzer.widgets.author.cards import CitationMetricsCard, IdentifiersCard, LastInstitutionCard
from pub_analyzer.widgets.author.tables import AuthorWorksByYearTable


class AuthorReportPane(VerticalScroll):
    """Work report Pane Widget."""

    DEFAULT_CSS = """
    AuthorReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }

    AuthorReportPane .table-container {
        margin: 1 0 0 0 ;
        height: auto;
    }
    """

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield LastInstitutionCard(author=self.report.author)
            yield IdentifiersCard(author=self.report.author)
            yield CitationMetricsCard(author=self.report.author)

        with Container(classes="table-container"):
            yield AuthorWorksByYearTable(author=self.report.author)
