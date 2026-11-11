"""Test the file picker used to choose an export directory or a report to load."""

from pathlib import Path

import pytest
from textual.widgets import Button

from pub_analyzer.widgets.common.filesystem import FileSystemSelector, PathSelectedBox
from tests.widgets.helpers import WidgetApp, node_path, open_file_picker, wait_until


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """A directory holding a `reports` subdirectory and a `notes.json` file."""
    (tmp_path / "reports").mkdir()
    (tmp_path / "notes.json").write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.fixture
def folder_with_reports(tmp_path: Path) -> Path:
    """A directory holding `folder/report.json`, `visible.json`, `excluded.txt` and two hidden entries."""
    (tmp_path / "folder").mkdir()
    (tmp_path / "folder" / "report.json").write_text("{}", encoding="utf-8")
    (tmp_path / "visible.json").write_text("{}", encoding="utf-8")
    (tmp_path / "excluded.txt").write_text("{}", encoding="utf-8")
    (tmp_path / ".hidden.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".hidden-directory").mkdir()
    return tmp_path


def shown_path(selector: FileSystemSelector) -> str:
    """Return the path the selector shows in its box."""
    return str(selector.query_one(PathSelectedBox).render())


@pytest.mark.asyncio
async def test_directory_picker_starts_on_its_directory(folder: Path) -> None:
    """The picker lists only directories, and Done can choose the starting directory right away."""
    selector = FileSystemSelector(folder, only_dir=True)
    app = WidgetApp(selector)

    async with app.run_test(size=(120, 50)) as pilot:
        picker, tree = await open_file_picker(pilot)

        assert [node_path(node) for node in tree.root.children] == [folder / "reports"]
        assert picker.path_selected == folder

        # Done closes the picker and reports the directory.
        assert await pilot.click("#done-button")
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert selector.path_selected == folder
        assert shown_path(selector) == folder.as_posix()
        assert app.selections == [folder]


@pytest.mark.asyncio
async def test_directory_picker_chooses_the_highlighted_directory(folder: Path) -> None:
    """Moving to a subdirectory highlights it, and Done chooses it."""
    selector = FileSystemSelector(folder, only_dir=True)
    app = WidgetApp(selector)

    async with app.run_test(size=(120, 50)) as pilot:
        picker, tree = await open_file_picker(pilot)

        tree.focus()
        await pilot.press("down")
        assert picker.path_selected == folder / "reports"

        assert await pilot.click("#done-button")
        await pilot.pause()

        assert selector.path_selected == folder / "reports"
        assert app.selections == [folder / "reports"]


@pytest.mark.asyncio
async def test_escape_keeps_the_previous_choice(folder: Path) -> None:
    """Closing the picker with Escape leaves the chosen directory as it was."""
    selector = FileSystemSelector(folder, only_dir=True)
    app = WidgetApp(selector)

    async with app.run_test(size=(120, 50)) as pilot:
        # Choose the subdirectory.
        _, tree = await open_file_picker(pilot)
        tree.focus()
        await pilot.press("down")
        assert await pilot.click("#done-button")
        await pilot.pause()

        # Open the picker again and close it with Escape.
        _, tree = await open_file_picker(pilot)
        tree.focus()
        await pilot.press("escape")
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert selector.path_selected == folder / "reports"
        assert shown_path(selector) == (folder / "reports").as_posix()
        assert app.selections == [folder / "reports"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["show_hidden", "expected"],
    [
        pytest.param(False, {"folder", "visible.json"}, id="hidden-entries-not-shown"),
        pytest.param(True, {"folder", "visible.json", ".hidden.json", ".hidden-directory"}, id="hidden-entries-shown"),
    ],
)
async def test_file_picker_lists_json_files_and_all_directories(folder_with_reports: Path, show_hidden: bool, expected: set[str]) -> None:
    """Only files with the wanted extension are listed, while every directory is, so they can be opened."""
    selector = FileSystemSelector(folder_with_reports, extension=[".json"], show_hidden_paths=show_hidden)

    async with WidgetApp(selector).run_test(size=(120, 50)) as pilot:
        _, tree = await open_file_picker(pilot)

        assert {node_path(node).name for node in tree.root.children} == expected


@pytest.mark.asyncio
async def test_file_picker_needs_a_file_to_be_chosen(folder_with_reports: Path) -> None:
    """Done stays disabled until a file is chosen; reopening the picker starts again from nothing."""
    selector = FileSystemSelector(folder_with_reports, extension=[".json"])
    app = WidgetApp(selector)
    report = folder_with_reports / "folder" / "report.json"

    async with app.run_test(size=(120, 50)) as pilot:
        picker, tree = await open_file_picker(pilot)
        done = picker.query_one("#done-button", Button)
        tree.focus()

        # Highlighting and opening a directory doesn't choose it.
        await pilot.press("home", "down")
        directory = tree.cursor_node
        assert node_path(directory) == folder_with_reports / "folder"
        assert done.disabled

        await pilot.press("enter")
        await wait_until(pilot, lambda: bool(directory and directory.children))

        # Highlighting a file doesn't choose it either; pressing Enter on it does.
        await pilot.press("down")
        assert node_path(tree.cursor_node) == report
        assert done.disabled

        await pilot.press("enter")
        assert picker.path_selected == report

        assert await pilot.click(done)
        await pilot.pause()
        assert selector.path_selected == report
        assert app.selections == [report]

        # The picker opens again with nothing chosen, and Escape keeps the previous file.
        picker, _ = await open_file_picker(pilot)
        assert picker.path_selected is None
        assert picker.query_one("#done-button", Button).disabled

        await pilot.press("escape")
        await pilot.pause()
        assert selector.path_selected == report
        assert app.selections == [report]


@pytest.mark.asyncio
async def test_closing_the_file_picker_chooses_nothing(folder_with_reports: Path) -> None:
    """Closing the picker with Escape before choosing a file leaves the selector empty."""
    selector = FileSystemSelector(folder_with_reports, extension=[".json"])
    app = WidgetApp(selector)

    async with app.run_test(size=(120, 50)) as pilot:
        await open_file_picker(pilot)
        await pilot.press("escape")
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert selector.path_selected is None
        assert shown_path(selector) == "..."
        assert app.selections == []
