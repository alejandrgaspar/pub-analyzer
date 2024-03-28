"""Topics Widgets."""

from urllib.parse import quote

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.topic import DehydratedTopic


class TopicsTable(Static):
    """All Topics from a work in a table."""

    DEFAULT_CSS = """
    TopicsTable .topics-table {
        height: auto;
        padding: 1 2 0 2;
    }
    """

    def __init__(self, topics_list: list[DehydratedTopic]) -> None:
        self.topics_list = topics_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        topics_table = Table(title="Topics", expand=True, show_lines=True)

        # Define Columns
        topics_table.add_column("", justify="center", vertical="middle")
        topics_table.add_column("Name", ratio=3)
        topics_table.add_column("Score", ratio=1)
        topics_table.add_column("Domain", ratio=1)
        topics_table.add_column("Field", ratio=1)
        topics_table.add_column("SubField", ratio=1)

        for idx, topic in enumerate(self.topics_list):
            name = f"""[@click=app.open_link('{quote(str(topic.id))}')][u]{topic.display_name}[/u][/]"""

            domain = f"""[@click=app.open_link('{quote(str(topic.domain.id))}')][u]{topic.domain.display_name}[/u][/]"""
            field = f"""[@click=app.open_link('{quote(str(topic.field.id))}')][u]{topic.field.display_name}[/u][/]"""
            subfield = f"""[@click=app.open_link('{quote(str(topic.subfield.id))}')][u]{topic.subfield.display_name}[/u][/]"""

            topics_table.add_row(
                str(idx),
                Text.from_markup(name, overflow="ellipsis"),
                Text.from_markup(f"{topic.score:.2f}"),
                Text.from_markup(domain),
                Text.from_markup(field),
                Text.from_markup(subfield),
            )

        yield Static(topics_table, classes="topics-table")
