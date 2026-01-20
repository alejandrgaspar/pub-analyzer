"""Locations Widgets."""

from urllib.parse import quote

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.work import Location


class LocationsTable(Static):
    """All Locations from a work in a table."""

    DEFAULT_CSS = """
    LocationsTable .locations-table {
        height: auto;
        padding: 1 2 0 2;
    }
    """

    def __init__(self, locations_list: list[Location]) -> None:
        self.locations_list = locations_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        locations_table = Table(title="Locations", expand=True, show_lines=True)

        # Define Columns
        locations_table.add_column("", justify="center", vertical="middle")
        locations_table.add_column("Name", ratio=3)
        locations_table.add_column("Publisher or institution", ratio=2)
        locations_table.add_column("Type")
        locations_table.add_column("ISSN-L")
        locations_table.add_column("Is OA")
        locations_table.add_column("License")
        locations_table.add_column("version")

        for idx, location in enumerate(self.locations_list):
            if location.source:
                source = location.source
                title = f"""[@click=app.open_link('{quote(str(location.landing_page_url))}')][u]{source.display_name}[/u][/]"""
                type = source.type or "-"
                issn_l = source.issn_l if source.issn_l else "-"

                if source.host_organization_name and source.host_organization:
                    publisher = (
                        f"""[@click=app.open_link('{quote(str(source.host_organization))}')][u]{source.host_organization_name}[/u][/]"""
                    )
                else:
                    publisher = source.host_organization_name if source.host_organization_name else "-"
            else:
                title = f"""[@click=app.open_link('{quote(str(location.landing_page_url))}')][u]{location.landing_page_url}[/u][/]"""
                publisher = "-"
                type = "-"
                issn_l = "-"

            is_open_access = "[#909d63]True[/]" if location.is_oa else "[#bc5653]False[/]"
            version = location.version.name if location.version else "-"
            license = location.license if location.license else "-"

            locations_table.add_row(
                str(idx),
                Text.from_markup(title, overflow="ellipsis"),
                Text.from_markup(publisher),
                Text.from_markup(type),
                Text.from_markup(issn_l),
                Text.from_markup(is_open_access),
                Text.from_markup(license),
                Text.from_markup(version.capitalize()),
            )

        yield Static(locations_table, classes="locations-table")
