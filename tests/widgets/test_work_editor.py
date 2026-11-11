"""Test editing a work's abstract from its details dialog."""

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, TextArea

from pub_analyzer.widgets.common import ReactiveLabel
from pub_analyzer.widgets.report.editor import TextEditor
from pub_analyzer.widgets.report.work import WorkModal, WorksTable
from tests.data.builders import make_author_report
from tests.widgets.helpers import WidgetApp, open_work_details, wait_until


async def open_editor(pilot: Pilot, details: WorkModal) -> TextArea:
    """Click the abstract's Edit button, and return the editor's text area."""
    edit = details.query_one("EditWidget Button", Button)
    edit.scroll_visible(animate=False)
    await pilot.pause()

    assert await pilot.click(edit)
    await wait_until(pilot, lambda: isinstance(pilot.app.screen, TextEditor))

    return pilot.app.screen.query_one(TextArea)


@pytest.mark.asyncio
async def test_saving_the_editor_updates_the_abstract() -> None:
    """Saved text replaces the abstract in the report and in the dialog."""
    report = make_author_report()
    table = WorksTable(report)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        details = await open_work_details(pilot, table)
        editor = await open_editor(pilot, details)
        assert editor.text == "Original abstract"

        # Add a line and save.
        editor.focus()
        await pilot.press("end", "!", "enter", "N", "e", "w")
        assert await pilot.click("#save")
        await pilot.pause()

        assert app.screen is details
        assert report.works[0].work.abstract == "Original abstract!\nNew"
        assert str(details.query_one(ReactiveLabel).render()) == "Original abstract!\nNew"

        # Opening the editor again shows the saved text.
        editor = await open_editor(pilot, details)
        assert editor.text == "Original abstract!\nNew"


@pytest.mark.asyncio
async def test_cancelling_the_editor_discards_the_changes() -> None:
    """Cancelled text is thrown away; the abstract stays as it was."""
    report = make_author_report()
    table = WorksTable(report)
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        details = await open_work_details(pilot, table)
        editor = await open_editor(pilot, details)

        # Change the text and cancel.
        editor.focus()
        await pilot.press("end", "!")
        assert await pilot.click("#cancel")
        await pilot.pause()

        assert app.screen is details
        assert report.works[0].work.abstract == "Original abstract"
        assert str(details.query_one(ReactiveLabel).render()) == "Original abstract"


@pytest.mark.asyncio
async def test_escape_closes_one_dialog_at_a_time() -> None:
    """Each Escape closes the top dialog and returns the focus to where it was before it opened."""
    table = WorksTable(make_author_report())
    app = WidgetApp(table)

    async with app.run_test(size=(140, 60)) as pilot:
        focus_target = app.query_one("#focus-target", Button)
        focus_target.focus()

        details = await open_work_details(pilot, table)
        await open_editor(pilot, details)

        # The first Escape closes the editor, returning to its Edit button.
        await pilot.press("escape")
        assert app.screen is details
        assert app.focused is details.query_one("EditWidget Button", Button)

        # The second closes the details, returning to where the focus was.
        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 1
        assert app.focused is focus_target
