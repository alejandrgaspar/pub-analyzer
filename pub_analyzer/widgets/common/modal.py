"""Modal Screen."""
from textual.screen import Screen


class Modal(Screen[None]):
    """Base overlay window container."""

    DEFAULT_CSS = """
    $bg-main-color: white;
    $bg-secondary-color: #e5e7eb;
    $text-primary-color: black;

    $text-primary-color-darken: black;

    Modal {
        background: rgba(229, 231, 235, 0.5);
        align: center middle;
    }

    Modal #dialog {
        background: $bg-main-color;
        height: 100%;
        width: 100%;

        margin: 3 10;
        border: $bg-secondary-color;
    }

    .-dark-mode Modal #dialog {
        background: $bg-secondary-color;
        color: $text-primary-color-darken;
    }

    Modal #dialog .dialog-title {
        height: 3;
        width: 100%;
        margin: 1;

        text-align: center;
        border-bottom: solid $text-primary-color;
    }
    """
