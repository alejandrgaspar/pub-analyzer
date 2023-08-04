"""Institution Report Widgets."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll

from pub_analyzer.models.report import InstitutionReport
from pub_analyzer.widgets.institution.cards import CitationMetricsCard, IdentifiersCard, RolesCard
from pub_analyzer.widgets.institution.tables import InstitutionWorksByYearTable


class InstitutionReportPane(VerticalScroll):
    """Work report Pane Widget."""

    DEFAULT_CSS = """
    InstitutionReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }

    InstitutionReportPane .table-container {
        margin: 1 0 0 0 ;
        height: auto;
    }
    """

    def __init__(self, report: InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield RolesCard(institution=self.report.institution)
            yield IdentifiersCard(institution=self.report.institution)
            yield CitationMetricsCard(institution=self.report.institution)

        with Container(classes="table-container"):
            yield InstitutionWorksByYearTable(institution=self.report.institution)
