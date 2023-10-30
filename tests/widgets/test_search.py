"""Test Search Widgets."""

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Button, Label

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets import search
from pub_analyzer.widgets.author.core import AuthorResumeWidget
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.institution.core import InstitutionResumeWidget
from tests.data.author import AUTHOR_RESULT_OBJECT
from tests.data.institution import INSTITUTION_RESULT_OBJECT


@pytest.mark.asyncio
async def test_author_search_bar_exit_focus() -> None:
    """Test sidebar toggle binding."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to AuthorFinder View.
        await pilot.click("#search-sidebar-button")
        search_bar = pilot.app.query_one(search.SearchBar)

        # Check search bar Focus
        assert pilot.app.focused is not search_bar
        pilot.app.set_focus(search_bar)
        assert pilot.app.focused is search_bar

        # Pressing esc key to unfocus search bar.
        await pilot.press("escape")
        assert pilot.app.focused is not search_bar


@pytest.mark.asyncio
async def test_author_result_complete_info() -> None:
    """Test Author result widget contains all info."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to Search View and mounting an author result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(search.AuthorResultWidget(AUTHOR_RESULT_OBJECT))

        # Check Info
        result_widget = pilot.app.query_one(search.AuthorResultWidget)

        assert str(result_widget.query_one(Button).label) == AUTHOR_RESULT_OBJECT.display_name

        assert str(AUTHOR_RESULT_OBJECT.cited_by_count) in str(result_widget.query_one(".cited-by-count", Label).renderable)
        assert str(AUTHOR_RESULT_OBJECT.works_count) in str(result_widget.query_one(".works-count", Label).renderable)
        assert str(AUTHOR_RESULT_OBJECT.external_id) in str(result_widget.query_one(".external-id", Label).renderable)

        assert str(AUTHOR_RESULT_OBJECT.hint or "") in str(result_widget.query_one(".text-hint", Label).renderable)


@pytest.mark.asyncio
async def test_institution_result_complete_info() -> None:
    """Test Institution result widget contains all info."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to Search View and mounting a institution result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(search.InstitutionResultWidget(INSTITUTION_RESULT_OBJECT))

        # Check Info
        result_widget = pilot.app.query_one(search.InstitutionResultWidget)

        assert str(result_widget.query_one(Button).label) == INSTITUTION_RESULT_OBJECT.display_name

        assert str(INSTITUTION_RESULT_OBJECT.cited_by_count) in str(result_widget.query_one(".cited-by-count", Label).renderable)
        assert str(INSTITUTION_RESULT_OBJECT.works_count) in str(result_widget.query_one(".works-count", Label).renderable)

        assert str(INSTITUTION_RESULT_OBJECT.hint or "") in str(result_widget.query_one(".text-hint", Label).renderable)


@pytest.mark.asyncio
async def test_author_result_button_redirect() -> None:
    """Test Author result widget button redirect to AuthorResumeWidget."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to FinderWidget View and mounting a result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(search.AuthorResultWidget(AUTHOR_RESULT_OBJECT))
        await pilot.wait_for_scheduled_animations()

        # Click author button.
        await pilot.click("AuthorResultWidget Button")

        # Check title update.
        title = pilot.app.query_one("#page-title", Label)
        assert str(title.renderable) == AUTHOR_RESULT_OBJECT.display_name

        # Check main content update.
        main_content = pilot.app.query_one(MainContent)
        main_content.get_child_by_type(AuthorResumeWidget)


@pytest.mark.asyncio
async def test_institution_result_button_redirect() -> None:
    """Test Institution result widget button redirect to InstitutionResumeWidget."""
    async with PubAnalyzerApp().run_test() as pilot:
        # Switch to FinderWidget View and mounting a result.
        await pilot.click("#search-sidebar-button")

        result_container = pilot.app.query_one("#results-container", VerticalScroll)
        await result_container.mount(search.InstitutionResultWidget(INSTITUTION_RESULT_OBJECT))
        await pilot.wait_for_scheduled_animations()

        # Click institution button.
        await pilot.click("InstitutionResultWidget Button")

        # Check title update.
        title = pilot.app.query_one("#page-title", Label)
        assert str(title.renderable) == INSTITUTION_RESULT_OBJECT.display_name

        # Check main content update.
        main_content = pilot.app.query_one(MainContent)
        main_content.get_child_by_type(InstitutionResumeWidget)
