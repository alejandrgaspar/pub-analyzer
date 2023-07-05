"""Card Widget."""

from textual.widgets import Static


class Card(Static):
    """Container for short, related pieces of content displayed in a box."""

    DEFAULT_CLASSES = "card"
    DEFAULT_CSS = """
    $bg-secondary-color: #e5e7eb;
    $text-primary-color: black;

    Card {
        layout: vertical;
        height: 100%;

        padding: 1 2;
        border: solid $text-primary-color;
        background: $bg-secondary-color;
    }

    Card > .card-title {
        margin: 0 0 1 0;
        width: 100%;
        text-align: center;
        border-bottom: solid black;
    }
    """
