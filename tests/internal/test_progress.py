"""Test report progress from pub_analyzer/internal/report/progress.py."""

import pytest

from pub_analyzer.internal.report.progress import ReportProgress, ReportStage, ignore_progress


@pytest.mark.parametrize(
    ["progress", "expected"],
    [
        pytest.param(ReportProgress(ReportStage.works), "Retrieving works...", id="works-unmeasured"),
        pytest.param(ReportProgress(ReportStage.citations, done=3, total=10), "Retrieving citations 3/10", id="citations"),
        pytest.param(ReportProgress(ReportStage.sources, done=0, total=4), "Retrieving sources 0/4", id="sources-at-start"),
        pytest.param(ReportProgress(ReportStage.sources, done=4, total=4), "Retrieving sources 4/4", id="sources-finished"),
        pytest.param(ReportProgress(ReportStage.citations, done=0, total=0), "Retrieving citations...", id="nothing-to-do"),
    ],
)
def test_description(progress: ReportProgress, expected: str) -> None:
    """Test ReportProgress.description property."""
    assert progress.description == expected


@pytest.mark.parametrize(
    ["progress", "expected"],
    [
        pytest.param(ReportProgress(ReportStage.citations, done=0, total=4), 0.0, id="at-start"),
        pytest.param(ReportProgress(ReportStage.citations, done=1, total=4), 25.0, id="quarter"),
        pytest.param(ReportProgress(ReportStage.citations, done=4, total=4), 100.0, id="finished"),
        pytest.param(ReportProgress(ReportStage.works), None, id="unknown-total"),
        pytest.param(ReportProgress(ReportStage.citations, done=0, total=0), None, id="empty-stage"),
    ],
)
def test_percentage(progress: ReportProgress, expected: float | None) -> None:
    """Test ReportProgress.percentage property."""
    assert progress.percentage == expected


@pytest.mark.parametrize(
    ["progress", "expected"],
    [
        pytest.param(ReportProgress(ReportStage.citations, done=0, total=1), True, id="known-total"),
        pytest.param(ReportProgress(ReportStage.works), False, id="no-total"),
        pytest.param(ReportProgress(ReportStage.works, total=0), False, id="zero-total"),
    ],
)
def test_is_measurable(progress: ReportProgress, expected: bool) -> None:
    """Test ReportProgress.is_measurable property."""
    assert progress.is_measurable is expected


def test_ignore_progress_accepts_anything() -> None:
    """The default callback does nothing and returns nothing."""
    assert ignore_progress(ReportProgress(ReportStage.works)) is None
