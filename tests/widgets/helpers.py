"""Helpers shared by the widget tests."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar
from unittest.mock import Mock

import pytest
from textual import on
from textual.app import App, ComposeResult
from textual.pilot import Pilot
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.widgets.directory_tree import DirEntry
from textual.widgets.tree import TreeNode

from pub_analyzer import main
from pub_analyzer.widgets.common.filesystem import FileSystemSelector, FilteredDirectoryTree, PathSelectedBox, PathSelectorModal
from pub_analyzer.widgets.report.work import WorkModal, WorksTable

CSS_DIR = Path(main.__file__).parent / "css"


class WidgetApp(App[None]):
    """Host a single widget with the app's theme and styles, but nothing else from the app.

    A `#focus-target` button gives tests somewhere to move the focus to.
    """

    CSS_PATH: ClassVar[list[Path]] = [CSS_DIR / "editor.tcss", CSS_DIR / "report.tcss", CSS_DIR / "tree.tcss"]

    def __init__(self, widget: Widget) -> None:
        super().__init__()
        self.register_theme(main.PUB_ANALYZER_THEME)
        self.theme = main.PUB_ANALYZER_THEME.name
        self.widget = widget
        self.selections: list[Path | None] = []
        """Paths reported by `FileSystemSelector.FileSelected` messages, in order."""

    def compose(self) -> ComposeResult:
        """Mount the focus target and the widget under test."""
        yield Button("Focus target", id="focus-target")
        yield self.widget

    @on(FileSystemSelector.FileSelected)
    def record_selection(self, event: FileSystemSelector.FileSelected) -> None:
        """Record the path a file selector reports."""
        self.selections.append(event.file_selected)


async def wait_until(pilot: Pilot, condition: Callable[[], bool]) -> None:
    """Wait up to 5 seconds for something the app does in the background, like opening a screen."""

    async def poll() -> None:
        while not condition():
            await pilot.pause(0.02)

    await asyncio.wait_for(poll(), timeout=5)
    await pilot.pause()


async def wait_for_workers(pilot: Pilot) -> None:
    """Wait up to 10 seconds for the app's background workers, like searches or report builders, to finish."""
    await asyncio.wait_for(pilot.app.workers.wait_for_complete(), timeout=10)
    await pilot.pause()


async def click_when_ready(pilot: Pilot, button: Button) -> None:
    """Click a button, after the effect of its previous press ends.

    Textual buttons ignore clicks while that effect (the `-active` class) is shown.
    """
    await wait_until(pilot, lambda: not button.has_class("-active"))
    assert await pilot.click(button)


def page_title(app: App) -> str:
    """Return the title shown above the main content."""
    return str(app.query_one("#page-title", Label).render())


def spy_on_notifications(app: App, monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Record the notifications the app shows, while still showing them."""
    notify = Mock(wraps=app.notify)
    monkeypatch.setattr(app, "notify", notify)
    return notify


async def open_file_picker(pilot: Pilot) -> tuple[PathSelectorModal, FilteredDirectoryTree]:
    """Open the file picker by clicking the selected-path box, and wait until it lists its directory."""
    assert await pilot.click(PathSelectedBox)
    await wait_until(pilot, lambda: isinstance(pilot.app.screen, PathSelectorModal))

    picker = pilot.app.screen
    assert isinstance(picker, PathSelectorModal)
    tree = picker.query_one(FilteredDirectoryTree)
    await wait_until(pilot, lambda: bool(tree.root.children))

    return picker, tree


async def open_work_details(pilot: Pilot, table: WorksTable, idx: int = 0) -> WorkModal:
    """Click a work's number in the works table, and return the details dialog it opens.

    The works table is a Rich table rendered as text, so its links are not widgets. To click
    one, look for the screen cell that carries its click action.

    Args:
        pilot: Pilot of the app showing the table.
        table: Works table, showing the page the work is on.
        idx: Position of the work in the report.
    """
    await pilot.pause()
    region = table.query_one(WorksTable._WorksTableRenderer).region.intersection(pilot.app.screen.region)

    for y in range(region.y, region.bottom):
        for x in range(region.x, region.right):
            if pilot.app.screen.get_style_at(x, y).meta.get("@click") == ("open_work_details", (idx,)):
                assert await pilot.click(offset=(x, y))
                await wait_until(pilot, lambda: isinstance(pilot.app.screen, WorkModal))

                details = pilot.app.screen
                assert isinstance(details, WorkModal)
                return details

    pytest.fail(f"Work {idx} has no clickable number on screen")


def node_path(node: TreeNode[DirEntry] | None) -> Path:
    """Return the path of an entry in the file picker."""
    assert node is not None
    assert node.data is not None
    return node.data.path
