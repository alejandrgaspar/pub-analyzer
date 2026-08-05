"""Orchestration of the requests and aggregation that make up a report."""

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
from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, AuthorYearCount, DehydratedAuthor
from pub_analyzer.models.institution import (
    DehydratedInstitution,
    Institution,
    InstitutionOpenAlexKey,
    InstitutionResult,
    InstitutionYearCount,
)
from pub_analyzer.models.report import AuthorReport, InstitutionReport, WorkReport
from pub_analyzer.models.source import Source
from pub_analyzer.models.work import Work


def _get_author_profiles_keys(
    author: Author, extra_profiles: list[Author | AuthorResult | DehydratedAuthor] | None
) -> list[AuthorOpenAlexKey]:
    """Create a list of profiles IDs joining main author profile and extra author profiles.

    Args:
        author: Main OpenAlex author object.
        extra_profiles: Extra OpenAlex authors objects related with the main author.

    Returns:
        List of Author OpenAlex Keys.
    """
    profiles: list[Author | AuthorResult | DehydratedAuthor] = [author, *(extra_profiles or [])]

    return [identifier.get_author_id(profile) for profile in profiles]


def _get_institution_keys(
    institution: Institution, extra_profiles: list[Institution | InstitutionResult | DehydratedInstitution] | None
) -> list[InstitutionOpenAlexKey]:
    """Create a list of profiles IDs joining main institution profile and extra institution profiles.

    Args:
        institution: Main OpenAlex institution object.
        extra_profiles: Extra OpenAlex institutions objects related with the main institution.

    Returns:
        List of Institution OpenAlex Keys.
    """
    profiles: list[Institution | InstitutionResult | DehydratedInstitution] = [institution, *(extra_profiles or [])]

    return [identifier.get_institution_id(profile) for profile in profiles]


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
    """
    url = build_works_url(
        filter_key=AUTHOR_FILTER_KEY,
        entity_keys=_get_author_profiles_keys(author, extra_profiles),
        from_date=pub_from_date,
        to_date=pub_to_date,
    )

    async with create_client() as http_client:
        client = OpenAlexClient(http_client)

        author_works = await client.get_works(url)
        works_reports = await _get_works_reports(client, author_works, cited_from_date, cited_to_date)
        sources = await _get_sources(client, author_works)

    author.counts_by_year = [AuthorYearCount(**counts._asdict()) for counts in aggregate.count_by_year(works_reports)]

    return AuthorReport(
        author=author,
        works=works_reports,
        citation_summary=aggregate.summarize_citations(works_reports),
        open_access_summary=aggregate.summarize_open_access(author_works),
        works_type_summary=aggregate.summarize_work_types(author_works),
        sources_summary=aggregate.build_sources_summary(sources),
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
    """
    url = build_works_url(
        filter_key=INSTITUTION_FILTER_KEY,
        entity_keys=_get_institution_keys(institution, extra_profiles),
        from_date=pub_from_date,
        to_date=pub_to_date,
    )

    async with create_client() as http_client:
        client = OpenAlexClient(http_client)

        institution_works = await client.get_works(url)
        works_reports = await _get_works_reports(client, institution_works, cited_from_date, cited_to_date)
        sources = await _get_sources(client, institution_works)

    institution.counts_by_year = [InstitutionYearCount(**counts._asdict()) for counts in aggregate.count_by_year(works_reports)]

    return InstitutionReport(
        institution=institution,
        works=works_reports,
        citation_summary=aggregate.summarize_citations(works_reports),
        open_access_summary=aggregate.summarize_open_access(institution_works),
        works_type_summary=aggregate.summarize_work_types(institution_works),
        sources_summary=aggregate.build_sources_summary(sources),
    )
