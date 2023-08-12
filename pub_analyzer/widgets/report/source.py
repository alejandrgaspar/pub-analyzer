"""Sources Report Widgets."""

import math
from urllib.parse import quote

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Static

from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.models.source import DehydratedSource


class SourcesTable(Static):
    """All Sources from an author in a table."""

    DEFAULT_CSS = """
    SourcesTable .sources-table {
        height: auto;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, sources_list: list[DehydratedSource]) -> None:
        self.sources_list = sources_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose table."""
        yield DataTable(zebra_stripes=True, header_height=2, id="sources-table")

    def on_mount(self) -> None:
        """Compose Table."""
        sources_table = self.query_one("#sources-table", DataTable)
        sources_table.cursor_type = "row"

        # Define Columns
        name_width = 70
        publisher_width = 60

        sources_table.add_column('Name', width=name_width)
        sources_table.add_column('Publisher or institution', width=publisher_width)
        sources_table.add_column('Type', width=10)
        sources_table.add_column('ISSN-L', width=10)
        sources_table.add_column('Is Open Access')

        for idx, source in enumerate(self.sources_list, start=1):
            if source.host_organization_name:
                host_organization = f"""[@click=app.open_link('{quote(str(source.host_organization))}')][u]{source.host_organization_name}[/u][/]"""  # noqa: E501
            else:
                host_organization = "-"

            title = f"""[@click=app.open_link('{quote(str(source.id))}')][u]{source.display_name}[/u][/]"""
            type_source = source.type
            issn_l = source.issn_l if source.issn_l else "-"
            is_open_access = "[#909d63]True[/]" if source.is_oa else "[#bc5653]False[/]"

            name_height = math.ceil(len(source.display_name) / name_width) + 1
            publisher_height = math.ceil(len(source.host_organization_name) / publisher_width) + 1 if source.host_organization_name else 1
            row_height = max(name_height, publisher_height)
            sources_table.add_row(
                Text.from_markup(title, overflow='ellipsis'),
                Text.from_markup(host_organization),
                Text.from_markup(type_source),
                Text.from_markup(issn_l),
                Text.from_markup(is_open_access),
                label=Text(f"{idx}", justify="center"),
                height=row_height,
            )


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
        yield SourcesTable(sources_list=self.report.sources_resume.sources)
