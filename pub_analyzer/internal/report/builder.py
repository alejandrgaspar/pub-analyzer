"""Orchestration of the requests and aggregation that make up a report."""

import math

import httpx
from pydantic import TypeAdapter
from textual import log

from pub_analyzer.internal import identifier
from pub_analyzer.internal.limiter import RateLimiter
from pub_analyzer.internal.openalex.parsing import get_valid_works
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

REQUEST_RATE_PER_SECOND = 8
"""The OpenAlex API requires a maximum of 10 requests per second. We limit this to 8 per second."""


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


async def _get_works(client: httpx.AsyncClient, url: str, limiter: RateLimiter) -> list[Work]:
    """Get all works given a URL.

    Iterate over all pages of the URL

    Args:
        client: HTTPX asynchronous client to be used to make the requests.
        url: URL of works with all filters and sorting applied.
        limiter: Rate limiter shared by every request of a report.

    Returns:
        List of Works Models.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    await limiter.acquire()
    response = await client.get(url=url, follow_redirects=True)
    response.raise_for_status()

    json_response = response.json()
    meta_info = json_response["meta"]
    page_count = math.ceil(meta_info["count"] / meta_info["per_page"])

    works_data = list(get_valid_works(json_response["results"]))

    for page_number in range(1, page_count):
        await limiter.acquire()
        page_result = (await client.get(url + f"&page={page_number + 1}", follow_redirects=True)).json()
        works_data.extend(get_valid_works(page_result["results"]))

    return TypeAdapter(list[Work]).validate_python(works_data)


async def _get_source(client: httpx.AsyncClient, url: str, limiter: RateLimiter) -> Source:
    """Get source given a URL.

    Args:
        client: HTTPX asynchronous client to be used to make the requests.
        url: URL of the source.
        limiter: Rate limiter shared by every request of a report.

    Returns:
        Source Model.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    await limiter.acquire()
    response = await client.get(url=url, follow_redirects=True)
    response.raise_for_status()

    json_response = response.json()
    hp_url = json_response["homepage_url"]
    if isinstance(hp_url, str):
        if not hp_url.startswith(("http", "https")):
            json_response["homepage_url"] = None
            log.warning(f"Discarted source homepage url: {url}")

    return Source(**json_response)


async def _get_works_reports(
    client: httpx.AsyncClient,
    limiter: RateLimiter,
    works: list[Work],
    cited_from_date: FromDate | None,
    cited_to_date: ToDate | None,
) -> list[WorkReport]:
    """Retrieve the citations of every work and classify them.

    Args:
        client: HTTPX asynchronous client to be used to make the requests.
        limiter: Rate limiter shared by every request of a report.
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
        citing_works = await _get_works(client, cited_by_url, limiter)

        works_reports.append(aggregate.build_work_report(work=work, citing_works=citing_works))

    return works_reports


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

    limiter = RateLimiter(rate=REQUEST_RATE_PER_SECOND, per_second=1.0)
    async with httpx.AsyncClient(http2=True, timeout=None) as client:
        author_works = await _get_works(client, url, limiter)
        works_reports = await _get_works_reports(client, limiter, author_works, cited_from_date, cited_to_date)

        # Get sources full info.
        sources: list[Source] = []
        dehydrated_sources = aggregate.collect_dehydrated_sources(author_works)
        sources_count = len(dehydrated_sources)
        for index, dehydrated_source in enumerate(dehydrated_sources, 1):
            source_id = identifier.get_source_id(dehydrated_source)

            log.info(f"Getting Sources... [{index}/{sources_count}]")
            sources.append(await _get_source(client, build_source_url(source_id), limiter))

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

    limiter = RateLimiter(rate=REQUEST_RATE_PER_SECOND, per_second=1.0)
    async with httpx.AsyncClient(http2=True, timeout=None) as client:
        institution_works = await _get_works(client, url, limiter)
        works_reports = await _get_works_reports(client, limiter, institution_works, cited_from_date, cited_to_date)

        # Get sources full info.
        sources = []
        dehydrated_sources = aggregate.collect_dehydrated_sources(institution_works)
        sources_count = len(dehydrated_sources)
        for index, dehydrated_source in enumerate(dehydrated_sources, 1):
            source_id = identifier.get_source_id(dehydrated_source)

            log.info(f"[{source_id}] Getting Sources... [{index}/{sources_count}]")

            # TODO(phase 2): make_author_report has no such guard, unify both once the
            # client layer grows retries and error handling.
            try:
                sources.append(await _get_source(client, build_source_url(source_id), limiter))
            except httpx.HTTPStatusError as exc:
                log.warning(f"Fail to retrive {source_id}: {exc}")

    institution.counts_by_year = [InstitutionYearCount(**counts._asdict()) for counts in aggregate.count_by_year(works_reports)]

    return InstitutionReport(
        institution=institution,
        works=works_reports,
        citation_summary=aggregate.summarize_citations(works_reports),
        open_access_summary=aggregate.summarize_open_access(institution_works),
        works_type_summary=aggregate.summarize_work_types(institution_works),
        sources_summary=aggregate.build_sources_summary(sources),
    )
