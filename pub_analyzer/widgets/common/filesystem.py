"""FileSystem Selector widgets."""

from collections.abc import Iterable
from enum import Enum, auto
from pathlib import Path

from rich.console import RenderableType
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label, Static, Tree
from textual.widgets._directory_tree import DirEntry

from .modal import Modal


class PathTypeSelector(Enum):
    """Expected path type to be selected."""

    FILE = auto()
    DIRECTORY = auto()


class FilteredDirectoryTree(DirectoryTree):
    """Directory Tree filtered."""

    def __init__(self, path: str | Path, *, show_hidden_paths: bool = False, only_dir: bool = False) -> None:
        self.show_hidden_paths = show_hidden_paths
        self.only_dir = only_dir
        super().__init__(path)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter paths with parameters specified in the class."""
        final_paths: list[Path] = []
        for path in paths:
            # Filter in case show hidden paths are not enable.
            if not self.show_hidden_paths and path.name.startswith("."):
                continue

            # Filter in case path type expected is directory.
            if not path.is_dir() and self.only_dir:
                continue

            final_paths.append(path)

        return final_paths


class PathSelectorModal(Modal[Path | None]):
    """Export modal confirmation."""

    DEFAULT_CSS = """
    $bg-main-color: white;
    $bg-secondary-color: #e5e7eb;

    PathSelectorModal FilteredDirectoryTree {
        background: $bg-main-color;
        width: 100%;
        margin: 0 2;
    }

    .-dark-mode PathSelectorModal FilteredDirectoryTree {
        background: $bg-secondary-color;
    }

    PathSelectorModal .button-container {
        height: 5;
        align: center middle;
    }
    """

    def __init__(self, path: str | Path, show_hidden_paths: bool = False, only_dir: bool = False) -> None:
        self.path = path
        self.show_hidden_paths = show_hidden_paths
        self.only_dir = only_dir

        self.path_selected: Path | None = None
        super().__init__()

    @on(events.Key)
    def exit_modal(self, message: events.Key) -> None:
        """Exit from the modal with esc KEY."""
        if message.key == 'escape':
            self.app.pop_screen()

    @on(Button.Pressed, "#done-button")
    def done_button(self) -> None:
        """Done button."""
        self.dismiss(self.path_selected)

    @on(DirectoryTree.FileSelected)
    def update_path_selected_for_file(self, event: DirectoryTree.FileSelected) -> None:
        """Update file selected."""
        if not self.only_dir:
            self.path_selected = event.path
            self.query_one("#done-button", Button).disabled = False

    @on(Tree.NodeHighlighted)
    def update_path_selected_for_dir(self, event: Tree.NodeHighlighted[DirEntry]) -> None:
        """Update file selected."""
        if self.only_dir and event.node and event.node.data:
            self.path_selected = event.node.data.path
            self.query_one("#done-button", Button).disabled = False

    def compose(self) -> ComposeResult:
        """Compose Modal."""
        with VerticalScroll(id='dialog'):
            yield Label("Export Path", classes='dialog-title')
            yield FilteredDirectoryTree(path=self.path, show_hidden_paths=self.show_hidden_paths, only_dir=self.only_dir)

            with Horizontal(classes="button-container"):
                yield Button("Done", variant="primary", disabled=True, id="done-button")


class PathSelectedBox(Widget):
    """Path selected box."""

    DEFAULT_CSS = """
    PathSelectedBox {
        height: 3;
        width: 100%;

        background: $boost;
        color: $text;

        padding: 0 2;
        border: tall $background;
    }
    """

    path_selected: reactive[str] = reactive("...", layout=True)

    class Selected(Message):
        """Selected message."""

    def on_click(self) -> None:
        """Post message on click."""
        self.post_message(self.Selected())

    def render(self) -> RenderableType:
        """Render path selected box."""
        return Text(self.path_selected, overflow="ellipsis")


class FileSystemSelector(Static):
    """File System selector widget."""

    class FileSelected(Message):
        """File Selected Message."""

        def __init__(self, file_selected: Path | None) -> None:
            self.file_selected = file_selected
            super().__init__()

    def __init__(self, path: str | Path, show_hidden_paths: bool = False, only_dir: bool = False) -> None:
        self.path = path
        self.show_hidden_paths = show_hidden_paths
        self.only_dir = only_dir

        self.path_selected: Path | None = None
        super().__init__()

    @on(PathSelectedBox.Selected)
    async def show_export_report_modal(self) -> None:
        """Show export Modal."""
        def update_file_selected(path: Path | None) -> None:
            """Call when modal is closed."""
            self.path_selected = path
            if path:
                self.query_one(PathSelectedBox).path_selected = path.as_posix()
                self.post_message(self.FileSelected(file_selected=path))
            else:
                self.query_one(PathSelectedBox).path_selected = "..."
                self.post_message(self.FileSelected(file_selected=path))

        await self.app.push_screen(
            PathSelectorModal(path=self.path, show_hidden_paths=self.show_hidden_paths, only_dir=self.only_dir),
            callback=update_file_selected
        )

    def compose(self) -> ComposeResult:
        """Compose file system selector."""
        yield PathSelectedBox()
