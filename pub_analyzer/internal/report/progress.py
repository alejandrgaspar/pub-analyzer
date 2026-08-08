"""Progress reported while a report is being built.

Building a report takes as long as the OpenAlex API needs to answer hundreds of
requests. These types let the caller follow along without the report internals knowing
anything about the interface displaying it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ReportStage(str, Enum):
    """Step of the report being worked on."""

    works = "works"
    """Listing the works belonging to the entity."""

    citations = "citations"
    """Retrieving the works that cite each of them."""

    sources = "sources"
    """Retrieving the full details of every source."""


_STAGE_DESCRIPTIONS = {
    ReportStage.works: "Retrieving works",
    ReportStage.citations: "Retrieving citations",
    ReportStage.sources: "Retrieving sources",
}


@dataclass(frozen=True)
class ReportProgress:
    """How far along a report is.

    Attributes:
        stage: Step being worked on.
        done: Steps finished so far.
        total: Steps to finish, or `None` while the amount of work is still unknown.
    """

    stage: ReportStage
    done: int = 0
    total: int | None = None

    @property
    def is_measurable(self) -> bool:
        """Whether the progress can be expressed as a fraction."""
        return self.total is not None and self.total > 0

    @property
    def percentage(self) -> float | None:
        """Share of this stage already finished, or `None` when it cannot be measured."""
        if not self.is_measurable:
            return None

        # `total` is not None here, but narrowing it keeps the type checker happy.
        return 100.0 * self.done / (self.total or 1)

    @property
    def description(self) -> str:
        """One line describing the current step, ready to display.

        Example:
            ```python
            ReportProgress(ReportStage.citations, done=3, total=10).description
            # 'Retrieving citations 3/10'
            ```
        """
        description = _STAGE_DESCRIPTIONS[self.stage]
        if not self.is_measurable:
            return f"{description}..."

        return f"{description} {self.done}/{self.total}"


ProgressCallback = Callable[[ReportProgress], None]
"""Called every time a report advances. Must not block: it runs on the event loop."""


def ignore_progress(progress: ReportProgress) -> None:
    """Discard progress updates, for callers that do not want them.

    Args:
        progress: Update being discarded.
    """
