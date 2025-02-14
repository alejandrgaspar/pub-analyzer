"""Test Body Widgets."""

import pytest
from textual.widgets import Label

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets.body import MainContent


@pytest.mark.anyio
async def test_main_content_update_title() -> None:
    """Test update title in MainContent Widget."""
    async with PubAnalyzerApp().run_test() as pilot:
        main_content = pilot.app.query_one(MainContent)

        new_title = "New Title"
        main_content.update_title(title=new_title)

        assert str(pilot.app.query_one("#page-title", Label).renderable) == new_title
