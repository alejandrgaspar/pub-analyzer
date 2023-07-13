"""Test Search Widgets."""

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Button, Label

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets.author.core import AuthorResumeWidget
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.search import AuthorResultWidget, AuthorSearchBar
from tests.data.author import AUTHOR_RESULT_OBJECT


@pytest.mark.asyncio
async def test_author_search_bar_exit_focus() -> None:
    """Test sidebar toggle binding."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to AuthorFinder View.
        await pilot.click("#search-sidebar-button")

        search_bar = pilot.app.query_one(AuthorSearchBar)
        pilot.app.set_focus(search_bar)

        # Pressing esc key to unfocus search bar.
        await pilot.press("escape")
        assert pilot.app.focused is None


@pytest.mark.asyncio
async def test_author_result_complete_info() -> None:
    """Test Author result widget contains all info."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to AuthorFinder View and mounting a result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(AuthorResultWidget(AUTHOR_RESULT_OBJECT))

        # Check Info
        result_widget = pilot.app.query_one(AuthorResultWidget)

        assert str(result_widget.query_one(Button).label) == AUTHOR_RESULT_OBJECT.display_name

        assert str(AUTHOR_RESULT_OBJECT.cited_by_count) in str(result_widget.query_one(".cited-by-count", Label).renderable)
        assert str(AUTHOR_RESULT_OBJECT.works_count) in str(result_widget.query_one(".works-count", Label).renderable)
        assert str(AUTHOR_RESULT_OBJECT.external_id) in str(result_widget.query_one(".external-id", Label).renderable)

        assert str(AUTHOR_RESULT_OBJECT.hint or '') in str(result_widget.query_one(".author-hint", Label).renderable)


@pytest.mark.asyncio
async def test_author_result_button_redirect() -> None:
    """Test Author result widget button redirect to AuthorResumeWidget."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to AuthorFinder View and mounting a result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(AuthorResultWidget(AUTHOR_RESULT_OBJECT))

        # Click author button.
        await pilot.click('AuthorResultWidget Button')

        # Check title update.
        title = pilot.app.query_one('#page-title', Label)
        assert str(title.renderable) == AUTHOR_RESULT_OBJECT.display_name

        # Check main content update.
        main_content = pilot.app.query_one(MainContent)
        main_content.get_child_by_type(AuthorResumeWidget)