"""Orchestration of the requests and aggregation that make up a report."""

from collections.abc import Callable, Sequence
from typing import NamedTuple, TypeVar

import httpx
from textual import log

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
from pub_analyzer.models.source import Source
from pub_analyzer.models.work import Work

ProfileT = TypeVar("ProfileT")
"""Any OpenAlex profile a report can be built from."""


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


async def _get_works_reports(
    client: OpenAlexClient,
    works: list[Work],
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
) -> list[WorkReport]:
    """Retrieve the citations of every work and classify them.

    Args:
        client: Client used to reach the OpenAlex API.
        works: Works being evaluated.
        cited_from_date: Filter citing works published from this date.
        cited_to_date: Filter citing works published up to this date.

    Returns:
        One report per evaluated work.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    works_reports: list[WorkReport] = []

    works_count = len(works)
    for index, work in enumerate(works, 1):
        work_id = identifier.get_work_id(work)
        log.info(f"[{work_id}] Work [{index}/{works_count}]")

        cited_by_url = build_cited_by_url(work_id, cited_from_date, cited_to_date)
        citing_works = await client.get_works(cited_by_url)

        works_reports.append(aggregate.build_work_report(work=work, citing_works=citing_works))

    return works_reports


async def _get_sources(client: OpenAlexClient, works: list[Work]) -> list[Source]:
    """Retrieve the full info of every source hosting the given works.

    Sources that cannot be retrieved are skipped: a single missing source is not worth
    discarding an otherwise complete report.

    Args:
        client: Client used to reach the OpenAlex API.
        works: Works whose locations point at the sources.

    Returns:
        Sources successfully retrieved.
    """
    sources: list[Source] = []

    dehydrated_sources = aggregate.collect_dehydrated_sources(works)
    sources_count = len(dehydrated_sources)
    for index, dehydrated_source in enumerate(dehydrated_sources, 1):
        source_id = identifier.get_source_id(dehydrated_source)
        log.info(f"[{source_id}] Getting Sources... [{index}/{sources_count}]")

        try:
            sources.append(await client.get_source(build_source_url(source_id)))
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            log.warning(f"Fail to retrive {source_id}: {exc}")

    return sources


async def _build_report(
    filter_key: str,
    entity_keys: Sequence[str],
    pub_from_date: FromDate | None,
    pub_to_date: ToDate | None,
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
) -> _ReportParts:
    """Retrieve everything a report needs and summarize it.

    Args:
        filter_key: OpenAlex filter selecting the entity, e.g. `"author.id"`.
        entity_keys: OpenAlex keys of the entity profiles the report covers.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter citing works published from this date.
        cited_to_date: Filter citing works published up to this date.

    Returns:
        The parts every report Model is assembled from.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    url = build_works_url(filter_key=filter_key, entity_keys=entity_keys, from_date=pub_from_date, to_date=pub_to_date)

    async with create_client() as http_client:
        client = OpenAlexClient(http_client)

        works = await client.get_works(url)
        works_reports = await _get_works_reports(client, works, cited_from_date, cited_to_date)
        sources = await _get_sources(client, works)

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
) -> AuthorReport:
    """Make a scientific production report by Author.

    Args:
        author: Author to whom the report is generated.
        extra_profiles: List of author profiles whose works will be attached.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter works that cite the author, published after this date.
        cited_to_date: Filter works that cite the author, published up to this date.

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
) -> InstitutionReport:
    """Make a scientific production report by Institution.

    Args:
        institution: Institution to which the report is generated.
        extra_profiles: List of institutions profiles whose works will be attached.

        pub_from_date: Filter works published from this date.
        pub_to_date: Filter works published up to this date.

        cited_from_date: Filter works that cite the institution, published after this date.
        cited_to_date: Filter works that cite the institution, published up to this date.

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
