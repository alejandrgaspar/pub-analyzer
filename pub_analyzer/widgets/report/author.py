"""Author Report Widgets."""

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import TabbedContent, TabPane

from pub_analyzer.models.report import AuthorReport
from pub_analyzer.widgets.author.cards import CitationMetricsCard, IdentifiersCard, LastInstitutionCard
from pub_analyzer.widgets.author.tables import AffiliationsTable, AuthorWorksByYearTable


class AuthorReportPane(VerticalScroll):
    """Work report Pane Widget."""

    DEFAULT_CSS = """
    AuthorReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;

        .author-tables-container {
            margin: 1 0 0 0 ;
            height: auto;
        }
    }
    """

    def __init__(self, report: AuthorReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield LastInstitutionCard(author=self.report.author)
            yield IdentifiersCard(author=self.report.author)
            yield CitationMetricsCard(author=self.report.author)

        with TabbedContent(id="author-tables-container"):
            with TabPane("Citation Metrics"):
                yield AuthorWorksByYearTable(author=self.report.author)
            with TabPane("Institutions"):
                yield AffiliationsTable(author=self.report.author)
