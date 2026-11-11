"""Regression tests for behavior that changed with Textual 8: the theme, text fields and links."""

from unittest.mock import AsyncMock, Mock

import pytest
from textual.widget import Widget
from textual.widgets import Button

from pub_analyzer.main import PUB_ANALYZER_THEME, PubAnalyzerApp
from pub_analyzer.widgets.common import Input
from pub_analyzer.widgets.common.input import DateInput
from pub_analyzer.widgets.report.export import ExportReportPane
from pub_analyzer.widgets.report.work import DownloadPane
from pub_analyzer.widgets.search import AuthorResultWidget, FinderWidget
from tests.data.author import AUTHOR_RESULT_OBJECT
from tests.data.builders import make_author_report, make_location
from tests.widgets.helpers import WidgetApp


def test_light_theme_is_set_before_mount() -> None:
    """The app's theme is set when the app is created.

    Switching from Textual's default dark theme after mounting animates every widget from
    dark colors, and some can get stuck with them.
    """
    app = PubAnalyzerApp()

    assert app.theme == PUB_ANALYZER_THEME.name
    assert not app.current_theme.dark


def text_field_host(field: str) -> Widget:
    """Build one of the app's text fields, or the widget that contains it."""
    report = make_author_report()

    match field:
        case "search":
            return FinderWidget()
        case "date":
            return DateInput()
        case "export":
            return ExportReportPane(report, suggest_prefix="author")
        case "download":
            location = make_location()
            location.pdf_url = "https://example.org/work.pdf"
            return DownloadPane(report.works[0], [location])

    raise ValueError(f"Unknown text field: {field}")


@pytest.mark.asyncio
@pytest.mark.usefixtures("home")
@pytest.mark.parametrize("field_name", ["search", "date", "export", "download"])
async def test_refocusing_a_text_field_keeps_its_text(field_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Focusing a field again places the cursor, instead of selecting all the text so typing replaces it."""
    # Typing in the search field would query OpenAlex.
    monkeypatch.setattr(FinderWidget, "lookup", AsyncMock())
    host = text_field_host(field_name)

    async with WidgetApp(host).run_test(size=(120, 50)) as pilot:
        field = host if isinstance(host, Input) else host.query_one(Input)
        field.value = "2020-01-01"

        # Focus the field, move the focus away, and come back.
        field.focus()
        await pilot.press("end")
        pilot.app.query_one("#focus-target", Button).focus()
        await pilot.pause()
        field.focus()
        await pilot.pause()

        # Typing adds to the text instead of replacing it.
        await pilot.press("x")
        assert field.value == "2020-01-01x"

        # Escape leaves the field.
        await pilot.press("escape")
        assert pilot.app.focused is not field


@pytest.mark.asyncio
async def test_external_link_opens_the_exact_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quotes, brackets, query strings and percent escapes in a link survive Textual's markup."""
    open_in_browser = Mock()
    monkeypatch.setattr("pub_analyzer.main.webbrowser.open", open_in_browser)

    url = "https://example.org/author?q=O'Reilly&title=[paper]&value=%25"
    result = AUTHOR_RESULT_OBJECT.model_copy(update={"external_id": url})

    async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
        await pilot.app.query_one("#results-container").mount(AuthorResultWidget(result))
        await pilot.pause()

        assert await pilot.click(".external-id")

    open_in_browser.assert_called_once_with(url)
