"""Test loading a saved report from a file."""

import gc
import threading
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter
from textual.pilot import Pilot
from textual.widgets import Button, Tab, TabbedContent

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.models.report import AuthorReport, CitationReport, CitationSummary, CitationType, InstitutionReport, WorkReport
from pub_analyzer.widgets.common import FileSystemSelector
from pub_analyzer.widgets.report import core
from pub_analyzer.widgets.report.core import AuthorReportWidget, InstitutionReportWidget, LoadReportWidget, ReportWidget, paused_gc
from pub_analyzer.widgets.report.work import WorksTable
from tests.data.author import AUTHOR
from tests.data.builders import make_author_report, make_institution_report, make_work
from tests.data.institution import INSTITUTION
from tests.widgets.helpers import click_when_ready, node_path, open_file_picker, page_title, spy_on_notifications, wait_until


async def open_loader(pilot: Pilot) -> LoadReportWidget:
    """Go to the Load report page through the sidebar."""
    assert await pilot.click("#load-sidebar-button")
    await wait_until(pilot, lambda: bool(pilot.app.query(LoadReportWidget)))

    return pilot.app.query_one(LoadReportWidget)


async def choose_institution_reports(pilot: Pilot, loader: LoadReportWidget) -> None:
    """Switch the loader from author to institution reports, with the keyboard."""
    loader.query_one(LoadReportWidget.EntityTypeSelector).focus()
    await pilot.press("enter", "down", "enter")

    assert loader.entity_handler is LoadReportWidget.EntityType.INSTITUTION


async def choose_file(pilot: Pilot, path: Path) -> None:
    """Choose `path`, which must be the only JSON file in the home directory, in the file picker."""
    _, tree = await open_file_picker(pilot)
    assert [node_path(node) for node in tree.root.children] == [path]

    tree.focus()
    await pilot.press("home", "down", "enter")
    assert await pilot.click("#done-button")
    await pilot.pause()


async def load_author_report(pilot: Pilot, path: Path) -> weakref.ref[AuthorReport]:
    """Load the author report at `path`, which must be the only JSON file in the home directory.

    Returns:
        Weak reference to the report shown, to tell whether it is freed.
    """
    loader = await open_loader(pilot)
    await choose_file(pilot, path)
    await click_when_ready(pilot, loader.query_one("#load-report-button", Button))
    await wait_until(pilot, lambda: bool(pilot.app.query(AuthorReportWidget)))

    return weakref.ref(pilot.app.query(AuthorReportWidget).first().report)


def block_parsing(monkeypatch: pytest.MonkeyPatch) -> tuple[threading.Event, threading.Event, threading.Event]:
    """Make reports wait to be parsed until released.

    Returns:
        Events set when parsing starts and when it ends, and the event that releases it.
    """
    started, ended, release = threading.Event(), threading.Event(), threading.Event()

    class BlockingTypeAdapter:
        """Parse like `TypeAdapter`, once released."""

        def __init__(self, report_type: type) -> None:
            self.adapter = TypeAdapter(report_type)

        def validate_json(self, data: bytes) -> Any:
            started.set()
            release.wait(timeout=5)
            try:
                return self.adapter.validate_json(data)
            finally:
                ended.set()

    monkeypatch.setattr(core, "TypeAdapter", BlockingTypeAdapter)
    return started, ended, release


def works_listed(pilot: Pilot) -> list[int]:
    """Return how many works each works table lists."""
    return [table.row_count for table in pilot.app.query(WorksTable)]


async def hide_empty_works(pilot: Pilot) -> None:
    """Open the Works tab and press ctrl+y, which hides the works without citations."""
    assert await pilot.click(next(tab for tab in pilot.app.query(Tab) if str(tab.label) == "Works"))
    await pilot.press("ctrl+y")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["make_report", "report_widget", "title"],
    [
        pytest.param(make_author_report, AuthorReportWidget, AUTHOR["display_name"], id="author"),
        pytest.param(make_institution_report, InstitutionReportWidget, INSTITUTION["display_name"], id="institution"),
    ],
)
async def test_loading_a_report_shows_it(
    make_report: Callable[[], AuthorReport | InstitutionReport],
    report_widget: type[AuthorReportWidget] | type[InstitutionReportWidget],
    title: str,
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The chosen report replaces the Load report page, with all its data and its title."""
    report = make_report()
    path = home / "résumé.json"
    path.write_text(report.model_dump_json(by_alias=True), encoding="utf-8")
    (home / "notes.txt").write_text("Not a report", encoding="utf-8")

    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        load_button = loader.query_one("#load-report-button", Button)
        assert page_title(app) == "Load report"
        assert load_button.disabled

        # Author reports are the default; institution reports have to be chosen.
        if isinstance(report, InstitutionReport):
            await choose_institution_reports(pilot, loader)

        await choose_file(pilot, path)
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: bool(app.query(report_widget)))

        # The report replaces the loader, with the same data it was saved with.
        loaded = app.query_one(report_widget)
        assert not app.query(LoadReportWidget)
        assert page_title(app) == title
        assert loaded.report.model_dump(mode="json", by_alias=True) == report.model_dump(mode="json", by_alias=True)
        assert loaded.query_one("#main-container", TabbedContent).tab_count == 4

    notify.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_report_shows_an_error_and_can_be_retried(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A report that doesn't match the chosen type is rejected, and the page stays ready to try again.

    Malformed JSON and a wrong schema fail validation in the same place as this case, an
    institution report loaded as an author report, so it covers them too.
    """
    path = home / "report.json"
    path.write_text(make_institution_report().model_dump_json(by_alias=True), encoding="utf-8")

    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        load_button = loader.query_one("#load-report-button", Button)
        await choose_file(pilot, path)

        # Loading it as an author report fails with an error message.
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: notify.called)

        assert notify.call_args.kwargs["title"] == "Error loading report!"
        assert notify.call_args.kwargs["severity"] == "error"

        # Nothing else changes, and the loader stops showing it is loading.
        assert app.query_one(LoadReportWidget) is loader
        assert not loader.loading
        assert not app.query(ReportWidget)
        assert page_title(app) == "Load report"
        assert loader.query_one(FileSystemSelector).path_selected == path

        # After fixing the file, loading it again works.
        report = make_author_report()
        path.write_text(report.model_dump_json(by_alias=True), encoding="utf-8")
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: bool(app.query(AuthorReportWidget)))

        assert app.query_one(AuthorReportWidget).report == report
        assert page_title(app) == report.author.display_name

    notify.assert_called_once()


@pytest.mark.asyncio
async def test_report_that_is_not_utf8_shows_an_error(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A report saved in another encoding, here Latin-1, is rejected like any other invalid report."""
    path = home / "report.json"
    path.write_bytes(make_author_report().model_dump_json(by_alias=True).encode("latin-1"))

    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        await choose_file(pilot, path)
        await click_when_ready(pilot, loader.query_one("#load-report-button", Button))
        await wait_until(pilot, lambda: notify.called)

        assert notify.call_args.kwargs["title"] == "Error loading report!"
        assert app.query_one(LoadReportWidget) is loader
        assert not app.query(ReportWidget)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "toggle_empty_works",
    [pytest.param(False, id="shown"), pytest.param(True, id="after-toggling-empty-works")],
)
async def test_closing_a_report_frees_it(toggle_empty_works: bool, home: Path) -> None:
    """Going to another page frees the report shown, whatever was done with it.

    Reports can take gigabytes of memory, so any reference left behind, like one in the cache
    Textual keeps of what `app.query_one` finds, adds up with each report loaded.
    """
    report = make_author_report()
    report.works.append(
        WorkReport(
            work=make_work("W2", title="Cited work"),
            cited_by=[CitationReport(work=make_work("W3"), citation_type=CitationType.TypeA)],
            citation_summary=CitationSummary(type_a_count=1),
        )
    )
    path = home / "report.json"
    path.write_text(report.model_dump_json(by_alias=True), encoding="utf-8")

    async with PubAnalyzerApp().run_test(size=(140, 60)) as pilot:
        loaded = await load_author_report(pilot, path)

        if toggle_empty_works:
            assert works_listed(pilot) == [2]
            await hide_empty_works(pilot)
            await wait_until(pilot, lambda: works_listed(pilot) == [1])

        assert await pilot.click("#search-sidebar-button")
        await wait_until(pilot, lambda: not pilot.app.query(ReportWidget))
        gc.collect()

        assert loaded() is None


@pytest.mark.asyncio
async def test_loading_pauses_the_garbage_collector(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The report is parsed with the garbage collector paused, and it resumes afterwards."""
    gc_enabled_while_parsing: list[bool] = []

    class SpyTypeAdapter:
        """Parse like `TypeAdapter`, recording whether the garbage collector is on."""

        def __init__(self, report_type: type) -> None:
            self.adapter = TypeAdapter(report_type)

        def validate_json(self, data: bytes) -> Any:
            gc_enabled_while_parsing.append(gc.isenabled())
            return self.adapter.validate_json(data)

    monkeypatch.setattr(core, "TypeAdapter", SpyTypeAdapter)
    path = home / "report.json"
    path.write_text(make_author_report().model_dump_json(by_alias=True), encoding="utf-8")

    async with PubAnalyzerApp().run_test(size=(140, 60)) as pilot:
        await load_author_report(pilot, path)

    assert gc_enabled_while_parsing == [False]
    assert gc.isenabled()


def test_paused_gc_resumes_the_collector_after_errors() -> None:
    """The collector resumes when what ran while it was paused fails, like parsing an invalid report."""
    with pytest.raises(ValueError), paused_gc():
        assert not gc.isenabled()
        raise ValueError

    assert gc.isenabled()


def test_paused_gc_leaves_the_collector_off_if_it_was_off() -> None:
    """Pausing the collector does not turn it on when it was off before."""
    gc.disable()
    try:
        with paused_gc():
            pass
        assert not gc.isenabled()
    finally:
        gc.enable()


@pytest.mark.asyncio
async def test_app_keeps_responding_while_a_report_loads(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reports are parsed in a thread, so the app keeps responding and shows the report is loading."""
    started, _, release = block_parsing(monkeypatch)
    path = home / "report.json"
    path.write_text(make_author_report().model_dump_json(by_alias=True), encoding="utf-8")

    async with PubAnalyzerApp().run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        await choose_file(pilot, path)
        await click_when_ready(pilot, loader.query_one("#load-report-button", Button))

        # Waiting runs the app, so this only returns if the app runs while the report is parsed.
        await wait_until(pilot, started.is_set)
        assert loader.loading
        assert not pilot.app.query(ReportWidget)

        release.set()
        await wait_until(pilot, lambda: bool(pilot.app.query(AuthorReportWidget)))


@pytest.mark.asyncio
async def test_going_elsewhere_while_a_report_loads_discards_it(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Going to another page while a report loads stays there, and the report is not shown once read."""
    started, ended, release = block_parsing(monkeypatch)
    path = home / "report.json"
    path.write_text(make_author_report().model_dump_json(by_alias=True), encoding="utf-8")

    async with PubAnalyzerApp().run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        await choose_file(pilot, path)
        await click_when_ready(pilot, loader.query_one("#load-report-button", Button))
        await wait_until(pilot, started.is_set)
        del loader

        assert await pilot.click("#search-sidebar-button")
        await wait_until(pilot, lambda: not pilot.app.query(LoadReportWidget))

        release.set()
        await wait_until(pilot, ended.is_set)
        await pilot.pause(0.2)

        assert page_title(pilot.app) == "Search"
        assert not pilot.app.query(ReportWidget)
