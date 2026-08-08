"""Orchestration of the requests and aggregation that make up a report."""

import asyncio
import logging
from collections.abc import Callable, Coroutine, Iterable, Sequence
from typing import Any, NamedTuple, TypeVar

import httpx

from pub_analyzer.internal import identifier
from pub_analyzer.internal.openalex.client import OpenAlexClient, create_client
from pub_analyzer.internal.openalex.urls import (
    AUTHOR_FILTER_KEY,
    INSTITUTION_FILTER_KEY,
    FromDate,
    ToDate,
    build_cited_by_url,
    build_source_url,
    build_works_url,
)
from pub_analyzer.internal.report import aggregate
from pub_analyzer.internal.report.progress import ProgressCallback, ReportProgress, ReportStage, ignore_progress
from pub_analyzer.models.author import Author, AuthorResult, AuthorYearCount, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionResult, InstitutionYearCount
from pub_analyzer.models.report import (
    AuthorReport,
    CitationSummary,
    InstitutionReport,
    OpenAccessSummary,
    SourcesSummary,
    WorkReport,
    WorkTypeCounter,
)
from pub_analyzer.models.source import DehydratedSource, Source
from pub_analyzer.models.work import Work

logger = logging.getLogger(__name__)

ProfileT = TypeVar("ProfileT")
"""Any OpenAlex profile a report can be built from."""

ResultT = TypeVar("ResultT")
"""Whatever one concurrent step of a report produces."""

MAX_CONCURRENT_REQUESTS = 10
"""How many requests of a report may be in flight at once.

The rate limiter still decides the pace; this only bounds how many connections and
pending responses are held open while waiting for it.
"""


class _ProgressCounter:
    """Counts finished steps so concurrent work still reports orderly progress."""

    def __init__(self, stage: ReportStage, total: int, on_progress: ProgressCallback) -> None:
        self.stage = stage
        self.total = total
        self.on_progress = on_progress
        self.done = 0

        self._report()

    def _report(self) -> None:
        """Hand the current state to the caller."""
        self.on_progress(ReportProgress(stage=self.stage, done=self.done, total=self.total))

    def advance(self, label: str) -> None:
        """Record one finished step.

        Args:
            label: What just finished, written to the log before the counter.
        """
        self.done += 1
        logger.info(f"{label} [{self.done}/{self.total}]")

        self._report()


async def _gather_bounded(
    coroutines: Iterable[Coroutine[Any, Any, ResultT]],
    limit: int = MAX_CONCURRENT_REQUESTS,
) -> list[ResultT]:
    """Run coroutines concurrently, keeping the results in the order they were given.

    Args:
        coroutines: Work to run.
        limit: How many may run at once.

    Returns:
        One result per coroutine, in input order.

    Raises:
        BaseException: The first failure, re-raised once every coroutine has settled.

    Danger:
        Failures surface only after everything else finishes. Bailing out early would
        leave requests running against a client that is about to be closed.
    """
    semaphore = asyncio.Semaphore(limit)

    async def bounded(coroutine: Coroutine[Any, Any, ResultT]) -> ResultT:
        async with semaphore:
            return await coroutine

    results = await asyncio.gather(*(bounded(coroutine) for coroutine in coroutines), return_exceptions=True)

    values: list[ResultT] = []
    for result in results:
        if isinstance(result, BaseException):
            raise result
        values.append(result)

    return values


class _ReportParts(NamedTuple):
    """Everything a report is made of, before it is attached to an entity.

    Author and institution reports differ only in the entity they describe and in the
    Model their year counts use, so the work of building one is shared.
    """

    works: list[WorkReport]
    citation_summary: CitationSummary
    open_access_summary: OpenAccessSummary
    works_type_summary: list[WorkTypeCounter]
    sources_summary: SourcesSummary
    counts_by_year: list[aggregate.YearCount]


def _get_profiles_keys(profiles: Sequence[ProfileT], get_id: Callable[[ProfileT], str]) -> list[str]:
    """Extract the OpenAlex key of every profile a report covers.

    Args:
        profiles: Main OpenAlex profile followed by the extra profiles whose works are attached.
        get_id: Extracts the OpenAlex key from a profile.

    Returns:
        List of OpenAlex Keys.
    """
    return [get_id(profile) for profile in profiles]


async def _get_citing_works(
    client: OpenAlexClient,
    work: Work,
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
) -> list[Work]:
    """Retrieve the works citing a given work.

    Args:
        client: Client used to reach the OpenAlex API.
        work: Work being evaluated.
        cited_from_date: Filter citing works published from this date.
        cited_to_date: Filter citing works published up to this date.

    Returns:
        Works citing the evaluated work.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    if work.cited_by_count < 1:
        return []

    cited_by_url = build_cited_by_url(identifier.get_work_id(work), cited_from_date, cited_to_date)

    return await client.get_works(cited_by_url)


async def _get_works_reports(
    client: OpenAlexClient,
    works: list[Work],
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
    on_progress: ProgressCallback,
) -> list[WorkReport]:
    """Retrieve the citations of every work and classify them.

    Args:
        client: Client used to reach the OpenAlex API.
        works: Works being evaluated.
        cited_from_date: Filter citing works published from this date.
        cited_to_date: Filter citing works published up to this date.
        on_progress: Called as each work is finished.

    Returns:
        One report per evaluated work, in the order the works were given.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    progress = _ProgressCounter(stage=ReportStage.citations, total=len(works), on_progress=on_progress)

    async def build_report(work: Work) -> WorkReport:
        citing_works = await _get_citing_works(client, work, cited_from_date, cited_to_date)
        progress.advance(f"[{identifier.get_work_id(work)}] Work")

        return aggregate.build_work_report(work=work, citing_works=citing_works)

    return await _gather_bounded(build_report(work) for work in works)


async def _get_sources(client: OpenAlexClient, works: list[Work], on_progress: ProgressCallback) -> list[Source]:
    """Retrieve the full info of every source hosting the given works.

    Sources that cannot be retrieved are skipped: a single missing source is not worth
    discarding an otherwise complete report.

    Args:
        client: Client used to reach the OpenAlex API.
        works: Works whose locations point at the sources.
        on_progress: Called as each source is finished.

    Returns:
        Sources successfully retrieved, in the order they were first seen.
    """
    dehydrated_sources = aggregate.collect_dehydrated_sources(works)
    progress = _ProgressCounter(stage=ReportStage.sources, total=len(dehydrated_sources), on_progress=on_progress)

    async def get_source(dehydrated_source: DehydratedSource) -> Source | None:
        source_id = identifier.get_source_id(dehydrated_source)
        try:
            source = await client.get_source(build_source_url(source_id))
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning(f"Fail to retrive {source_id}: {exc}")
            progress.advance(f"[{source_id}] Skipped source")
            return None

        progress.advance(f"[{source_id}] Getting Sources...")

        return source

    retrieved = await _gather_bounded(get_source(dehydrated_source) for dehydrated_source in dehydrated_sources)

    return [source for source in retrieved if source is not None]


async def _build_report(
    filter_key: str,
    entity_keys: Sequence[str],
    pub_from_date: FromDate | None,
    pub_to_date: ToDate | None,
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
    on_progress: ProgressCallback,
) -> _ReportParts:
    """Retrieve everything a report needs and summarize it.

    Args:
        filter_key: OpenAlex filter selecting the entity, e.g. `"author.id"`.
        entity_keys: OpenAlex keys of the entity profiles the report covers.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter citing works published from this date.
        cited_to_date: Filter citing works published up to this date.

        on_progress: Called as the report advances.

    Returns:
        The parts every report Model is assembled from.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    url = build_works_url(filter_key=filter_key, entity_keys=entity_keys, from_date=pub_from_date, to_date=pub_to_date)

    async with create_client() as http_client:
        client = OpenAlexClient(http_client)

        # How many works there are is only known once the listing comes back.
        on_progress(ReportProgress(stage=ReportStage.works))
        works = await client.get_works(url)

        works_reports = await _get_works_reports(client, works, cited_from_date, cited_to_date, on_progress)
        sources = await _get_sources(client, works, on_progress)

    return _ReportParts(
        works=works_reports,
        citation_summary=aggregate.summarize_citations(works_reports),
        open_access_summary=aggregate.summarize_open_access(works),
        works_type_summary=aggregate.summarize_work_types(works),
        sources_summary=aggregate.build_sources_summary(sources),
        counts_by_year=aggregate.count_by_year(works_reports),
    )


async def make_author_report(
    author: Author,
    extra_profiles: list[Author | AuthorResult | DehydratedAuthor] | None = None,
    pub_from_date: FromDate | None = None,
    pub_to_date: ToDate | None = None,
    cited_from_date: FromDate | None = None,
    cited_to_date: ToDate | None = None,
    on_progress: ProgressCallback = ignore_progress,
) -> AuthorReport:
    """Make a scientific production report by Author.

    Args:
        author: Author to whom the report is generated.
        extra_profiles: List of author profiles whose works will be attached.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter works that cite the author, published after this date.
        cited_to_date: Filter works that cite the author, published up to this date.

        on_progress: Called as the report advances, to follow a long running report.

    Returns:
        Author's scientific production report Model.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.

    Info:
        The Author in the report carries the year counts observed while building it, which
        respect the date filters applied. The Author passed in is left untouched.
    """
    profiles: list[Author | AuthorResult | DehydratedAuthor] = [author, *(extra_profiles or [])]

    parts = await _build_report(
        filter_key=AUTHOR_FILTER_KEY,
        entity_keys=_get_profiles_keys(profiles, identifier.get_author_id),
        pub_from_date=pub_from_date,
        pub_to_date=pub_to_date,
        cited_from_date=cited_from_date,
        cited_to_date=cited_to_date,
        on_progress=on_progress,
    )

    counts_by_year = [AuthorYearCount(**counts._asdict()) for counts in parts.counts_by_year]

    return AuthorReport(
        author=author.model_copy(update={"counts_by_year": counts_by_year}),
        works=parts.works,
        citation_summary=parts.citation_summary,
        open_access_summary=parts.open_access_summary,
        works_type_summary=parts.works_type_summary,
        sources_summary=parts.sources_summary,
    )


async def make_institution_report(
    institution: Institution,
    extra_profiles: list[Institution | InstitutionResult | DehydratedInstitution] | None = None,
    pub_from_date: FromDate | None = None,
    pub_to_date: ToDate | None = None,
    cited_from_date: FromDate | None = None,
    cited_to_date: ToDate | None = None,
    on_progress: ProgressCallback = ignore_progress,
) -> InstitutionReport:
    """Make a scientific production report by Institution.

    Args:
        institution: Institution to which the report is generated.
        extra_profiles: List of institutions profiles whose works will be attached.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter works that cite the institution, published after this date.
        cited_to_date: Filter works that cite the institution, published up to this date.

        on_progress: Called as the report advances, to follow a long running report.

    Returns:
        Institution's scientific production report Model.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.

    Info:
        The Institution in the report carries the year counts observed while building it,
        which respect the date filters applied. The Institution passed in is left untouched.
    """
    profiles: list[Institution | InstitutionResult | DehydratedInstitution] = [institution, *(extra_profiles or [])]

    parts = await _build_report(
        filter_key=INSTITUTION_FILTER_KEY,
        entity_keys=_get_profiles_keys(profiles, identifier.get_institution_id),
        pub_from_date=pub_from_date,
        pub_to_date=pub_to_date,
        cited_from_date=cited_from_date,
        cited_to_date=cited_to_date,
        on_progress=on_progress,
    )

    counts_by_year = [InstitutionYearCount(**counts._asdict()) for counts in parts.counts_by_year]

    return InstitutionReport(
        institution=institution.model_copy(update={"counts_by_year": counts_by_year}),
        works=parts.works,
        citation_summary=parts.citation_summary,
        open_access_summary=parts.open_access_summary,
        works_type_summary=parts.works_type_summary,
        sources_summary=parts.sources_summary,
    )
