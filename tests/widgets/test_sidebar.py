"""Test Sidebar Widget."""

import sys
from typing import TypeVar

import pytest
from textual.widget import Widget

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.report.core import LoadReportWidget
from pub_analyzer.widgets.search import FinderWidget

ExpectType = TypeVar("ExpectType", bound="Widget")


if sys.platform == "win32":
    pytest.skip(
        "Skipping this module on Windows. GH runners for Windows are not reliable for verifying these types of tests.",
        allow_module_level=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["button_id", "widget_expected"],
    [
        ["#search-sidebar-button", FinderWidget],
        ["#load-sidebar-button", LoadReportWidget],
    ],
)
async def test_sidebar_menu_options(button_id: str, widget_expected: type[ExpectType]) -> None:
    """Test sidebar options update Main content correctly."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Get main content container
        main_content = pilot.app.query_one(MainContent)

        # Click sidebar option
        await pilot.click(button_id)

        # Search widget by Type if not found then raise error
        main_content.get_child_by_type(widget_expected)
