"""Grants Widgets."""

from urllib.parse import quote

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.work import Award, Grant


class GrantsTable(Static):
    """All Grants from a work in a table."""

    DEFAULT_CSS = """
    GrantsTable .grants-table {
        height: auto;
        padding: 1 2 0 2;
    }
    """

    def __init__(self, grants_list: list[Grant]) -> None:
        self.grants_list = grants_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        grants_table = Table(title="Grants", expand=True, show_lines=True)

        # Define Columns
        grants_table.add_column("", justify="center", vertical="middle")
        grants_table.add_column("Name", ratio=3)
        grants_table.add_column("Award ID", ratio=2)

        for idx, grant in enumerate(self.grants_list):
            name = f"""[@click=app.open_link('{quote(str(grant.funder))}')][u]{grant.funder_display_name}[/u][/]"""
            award_id = grant.award_id or "-"

            grants_table.add_row(
                str(idx),
                Text.from_markup(name, overflow="ellipsis"),
                Text.from_markup(award_id),
            )

        yield Static(grants_table, classes="grants-table")


class AwardsTable(Static):
    """Grants or funding awards that support research."""

    DEFAULT_CSS = """
    GrantsTable .grants-table {
        height: auto;
        padding: 1 2 0 2;
    }
    """

    def __init__(self, awards_list: list[Award]) -> None:
        self.awards_list = awards_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        awards_table = Table(title="Awards", expand=True, show_lines=True)

        # Define Columns
        awards_table.add_column("", justify="center", vertical="middle")
        awards_table.add_column("Name", ratio=3)
        awards_table.add_column("Award ID", ratio=2)
        awards_table.add_column("DOI", ratio=2)

        for idx, award in enumerate(self.awards_list):
            name = f"""[@click=app.open_link('{quote(str(award.funder_award_id))}')][u]{award.funder_display_name}[/u][/]"""
            award_id = award.display_name or "-"
            doi = f"""[@click=app.open_link('{quote(str(award.doi))}')][u]{award.doi}[/u][/]""" if award.doi else "-"

            awards_table.add_row(
                str(idx),
                Text.from_markup(name, overflow="ellipsis"),
                Text.from_markup(award_id),
                Text.from_markup(doi, overflow="ellipsis"),
            )

        yield Static(awards_table, classes="grants-table")
