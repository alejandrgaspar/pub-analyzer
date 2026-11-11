"""Sources Report Widgets."""

from typing import ClassVar
from urllib.parse import quote

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll

from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.models.source import Source
from pub_analyzer.widgets.common import PaginatedTable


class SourcesTable(PaginatedTable):
    """All Sources from an author in a table, a page at a time."""

    DEFAULT_CSS = """
    SourcesTable {
        margin: 1 0 0 0;
    }
    """

    ROWS_NAME: ClassVar[str] = "Sources"

    def __init__(self, sources_list: list[Source]) -> None:
        self.sources_list = sources_list
        super().__init__()

    @property
    def row_count(self) -> int:
        """Number of sources, across all pages."""
        return len(self.sources_list)

    def build_table(self) -> Table:
        """Build the table of the sources on the page shown."""
        sources_table = Table(title="Sources", expand=True, show_lines=True)

        # Define Columns
        sources_table.add_column("", justify="center", vertical="middle")
        sources_table.add_column("Name", ratio=3)
        sources_table.add_column("Publisher or institution", ratio=2)
        sources_table.add_column("Type")
        sources_table.add_column("ISSN-L")
        sources_table.add_column("Impact factor")
        sources_table.add_column("h-index")
        sources_table.add_column("Is OA")

        for idx in self.page_rows:
            source = self.sources_list[idx]
            if source.host_organization_name:
                host_organization = (
                    f"""[@click=app.open_link('{quote(str(source.host_organization))}')][u]{source.host_organization_name}[/u][/]"""
                )
            else:
                host_organization = "-"

            title = f"""[@click=app.open_link('{quote(str(source.id))}')][u]{source.display_name}[/u][/]"""
            type_source = source.type or "-"
            issn_l = source.issn_l if source.issn_l else "-"
            impact_factor = f"{source.summary_stats.two_yr_mean_citedness:.3f}"
            h_index = f"{source.summary_stats.h_index}"

            is_open_access = "[#909d63]True[/]" if source.is_oa else "[#bc5653]False[/]"

            sources_table.add_row(
                str(idx),
                Text.from_markup(title, overflow="ellipsis"),
                Text.from_markup(host_organization),
                Text.from_markup(type_source),
                Text.from_markup(issn_l),
                Text.from_markup(impact_factor),
                Text.from_markup(h_index),
                Text.from_markup(is_open_access),
            )

        return sources_table


class SourcesReportPane(VerticalScroll):
    """Sources report Pane Widget."""

    DEFAULT_CSS = """
    SourcesReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }
    """

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        yield SourcesTable(sources_list=self.report.sources_summary.sources)
