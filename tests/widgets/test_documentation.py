"""Guard the private Textual formatter used by the MkDocs getting-started page."""

from pathlib import Path
from xml.etree import ElementTree

from textual._doc import format_svg

from pub_analyzer import main


def test_documentation_screenshot_formatter() -> None:
    """The formatter must render the app, not silently replace the fence with empty HTML."""
    svg = format_svg("", "textual", "textual", {}, None, {"path": str(Path(main.__file__)), "columns": "90"})
    assert "<svg" in svg
    assert "Pub Analyzer" in "".join(ElementTree.fromstring(svg).itertext()).replace("\N{NO-BREAK SPACE}", " ")
