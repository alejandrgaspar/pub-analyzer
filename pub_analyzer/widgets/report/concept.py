"""Concepts Widgets."""

from urllib.parse import quote

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.concept import DehydratedConcept


class ConceptsTable(Static):
    """All Concepts from a work in a table."""

    DEFAULT_CSS = """
    ConceptsTable .concepts-table {
        height: auto;
        padding: 1 2 0 2;
    }
    """

    def __init__(self, concepts_list: list[DehydratedConcept]) -> None:
        self.concepts_list = concepts_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        concepts_table = Table(title="Concepts", expand=True, show_lines=True)

        # Define Columns
        concepts_table.add_column("", justify="center", vertical="middle")
        concepts_table.add_column("Name", ratio=5)
        concepts_table.add_column("Score", ratio=1)
        concepts_table.add_column("Level", ratio=1)

        for idx, concept in enumerate(self.concepts_list):
            name = f"""[@click=app.open_link('{quote(str(concept.wikidata))}')][u]{concept.display_name}[/u][/]"""

            concepts_table.add_row(
                str(idx),
                Text.from_markup(name, overflow="ellipsis"),
                Text.from_markup(f"{concept.score:.2f}"),
                Text.from_markup(f"{concept.level:.1f}"),
            )

        yield Static(concepts_table, classes="concepts-table")
