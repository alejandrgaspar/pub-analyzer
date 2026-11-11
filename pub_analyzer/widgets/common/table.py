"""Paginated Table Widget."""

import math
from typing import ClassVar

from rich.table import Table
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Label, Static


class PaginatedTable(Static):
    """Rich table shown a page at a time, with buttons to change page.

    A Rich table is a single renderable, so rendering it takes time in proportion to its
    rows. Reports can have thousands of rows, so only one page of them is rendered.

    Subclasses say how many rows there are, and build the table of the rows in `page_rows`.
    """

    DEFAULT_CSS = """
    PaginatedTable {
        height: auto;

        .table-pager {
            height: auto;
            align: center middle;

            Button {
                margin: 0 1;
            }

            Label {
                height: 3;
                content-align: center middle;
                padding: 0 2;
            }
        }
    }
    """

    PAGE_SIZE: ClassVar[int] = 50
    """Rows shown on each page."""

    ROWS_NAME: ClassVar[str] = "Rows"
    """What the rows are, to describe the page shown."""

    page: reactive[int] = reactive(0, init=False)
    """Zero-based number of the page shown."""

    @property
    def row_count(self) -> int:
        """Number of rows, across all pages."""
        raise NotImplementedError

    def build_table(self) -> Table:
        """Build the table of the rows in `page_rows`."""
        raise NotImplementedError

    def make_table_widget(self, table: Table) -> Static:
        """Create the widget that shows the table, which subclasses can override to handle its links."""
        return Static(table)

    @property
    def page_count(self) -> int:
        """Number of pages, which is at least one even when there are no rows."""
        return max(1, math.ceil(self.row_count / self.PAGE_SIZE))

    @property
    def page_rows(self) -> range:
        """Positions of the rows on the page shown."""
        start = self.page * self.PAGE_SIZE
        return range(start, min(start + self.PAGE_SIZE, self.row_count))

    def compose(self) -> ComposeResult:
        """Compose the table of the first page, and the buttons to change page."""
        table_widget = self.make_table_widget(self.build_table())
        table_widget.add_class("table-content")
        # Highlighting a link on hover renders the whole table again, which stalls long tables.
        # This also drops the CSS link style, so links must be underlined in their markup.
        table_widget.auto_links = False
        yield table_widget

        with Horizontal(classes="table-pager"):
            yield Button("First", id="first-page")
            yield Button("Previous", id="previous-page")
            yield Label(id="page-label")
            yield Button("Next", id="next-page")
            yield Button("Last", id="last-page")

    def on_mount(self) -> None:
        """Show which page is shown."""
        self.update_pager()

    def validate_page(self, page: int) -> int:
        """Keep the page within the pages there are."""
        return min(max(page, 0), self.page_count - 1)

    def watch_page(self) -> None:
        """Show the table of the new page, from its top."""
        self.query_one(".table-content", Static).update(self.build_table())
        self.update_pager()
        self.call_after_refresh(self.scroll_visible, top=True, animate=False)

    @on(Button.Pressed, "#first-page")
    def show_first_page(self, event: Button.Pressed) -> None:
        """Show the first page."""
        event.stop()
        self.page = 0

    @on(Button.Pressed, "#previous-page")
    def show_previous_page(self, event: Button.Pressed) -> None:
        """Show the previous page."""
        event.stop()
        self.page -= 1

    @on(Button.Pressed, "#next-page")
    def show_next_page(self, event: Button.Pressed) -> None:
        """Show the next page."""
        event.stop()
        self.page += 1

    @on(Button.Pressed, "#last-page")
    def show_last_page(self, event: Button.Pressed) -> None:
        """Show the last page."""
        event.stop()
        self.page = self.page_count - 1

    def update_pager(self) -> None:
        """Show the page number, and disable the buttons that lead past the first or last page.

        The pager is hidden when every row fits on one page.
        """
        self.query_one(".table-pager").display = self.page_count > 1

        on_first_page = self.page == 0
        on_last_page = self.page == self.page_count - 1
        self.query_one("#first-page", Button).disabled = on_first_page
        self.query_one("#previous-page", Button).disabled = on_first_page
        self.query_one("#next-page", Button).disabled = on_last_page
        self.query_one("#last-page", Button).disabled = on_last_page

        rows = self.page_rows
        self.query_one("#page-label", Label).update(
            f"Page {self.page + 1} of {self.page_count} · {self.ROWS_NAME} {rows.start + 1}-{rows.stop} of {self.row_count}"
        )
