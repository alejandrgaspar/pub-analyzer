"""Functions to make reports."""

import datetime
import math
from typing import Any, NewType

import httpx
from pydantic import TypeAdapter

from pub_analyzer.internal import identifier
from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionOpenAlexKey, InstitutionResult
from pub_analyzer.models.report import (
    AuthorReport,
    CitationReport,
    CitationSummary,
    CitationType,
    InstitutionReport,
    OpenAccessSummary,
    SourcesSummary,
    WorkReport,
    WorkTypeCounter,
)
from pub_analyzer.models.source import DehydratedSource, Source
from pub_analyzer.models.work import Authorship, Work

FromDate = NewType("FromDate", datetime.datetime)
"""DateTime marker for works published from this date."""

ToDate = NewType("ToDate", datetime.datetime)
"""DateTime marker for works published up to this date."""


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
    if extra_profiles:
        profiles = [author, *extra_profiles]
        return [identifier.get_author_id(profile) for profile in profiles]
    else:
        return [identifier.get_author_id(author)]


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
    if extra_profiles:
        profiles = [institution, *extra_profiles]
        return [identifier.get_institution_id(profile) for profile in profiles]
    else:
        return [identifier.get_institution_id(institution)]


def _get_authors_list(authorships: list[Authorship]) -> list[str]:
    """Collect OpenAlex IDs from authors in a list of authorships.

    Args:
        authorships: List of authorships.

    Returns:
        Authors keys IDs.
    """
    return [identifier.get_author_id(authorship.author) for authorship in authorships]


def _get_citation_type(original_work_authors: list[str], cited_work_authors: list[str]) -> CitationType:
    """Compare two lists of authors and returns the citation type.

    Based on the authors of a given work and the authors of another work that cites the analyzed work,
    calculate the citation type.

    Args:
        original_work_authors: List of the authors of the evaluated work.
        cited_work_authors: List of the authors of the citing document.

    Returns:
        Calculated cite type (Type A or Type B).

    Info:
        **Type A:** Citations made by researchers in documents where the evaluated author or
        one of his co-authors does not appear as part of the authorship of the citing documents.

        **Type B:** Citations generated by the author or one of the co-authors of the work being
        analyzed.
    """
    original_set = set(original_work_authors)
    cited_set = set(cited_work_authors)

    return CitationType.TypeA if not original_set.intersection(cited_set) else CitationType.TypeB


def _add_work_abstract(work: dict[str, Any]) -> dict[str, Any]:
    """Get work abtract from abstract_inverted_index and insert new key `abstract`.

    Args:
        work: Raw work.

    Returns:
        Work with new key `abstract`.
    """
    abstract_inverted_index = work.get("abstract_inverted_index")
    if abstract_inverted_index:
        work["abstract"] = " ".join(abstract_inverted_index)
    else:
        work["abstract"] = None
    return work


def _get_valid_works(works: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Skip works that do not contain enough data.

    Args:
        works: List of raw works.

    Returns:
        List of raw works with enough data to pass the Works validation.

    Danger:
        Sometimes OpenAlex provides works with insufficient information to be considered.
        In response, we have chosen to exclude such works at this stage, thus avoiding
        the need to handle exceptions within the Model validators.
    """
    return [_add_work_abstract(work) for work in works if work["title"] is not None]


async def _get_works(client: httpx.AsyncClient, url: str) -> list[Work]:
    """Get all works given a URL.

    Iterate over all pages of the URL

    Args:
        client: HTTPX asynchronous client to be used to make the requests.
        url: URL of works with all filters and sorting applied.

    Returns:
        List of Works Models.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    response = await client.get(url=url)
    response.raise_for_status()

    json_response = response.json()
    meta_info = json_response["meta"]
    page_count = math.ceil(meta_info["count"] / meta_info["per_page"])

    works_data = list(_get_valid_works(json_response["results"]))

    for page_number in range(1, page_count):
        page_result = (await client.get(url + f"&page={page_number + 1}")).json()
        works_data.extend(_get_valid_works(page_result["results"]))

    return TypeAdapter(list[Work]).validate_python(works_data)


async def _get_source(client: httpx.AsyncClient, url: str) -> Source:
    """Get source given a URL.

    Args:
        client: HTTPX asynchronous client to be used to make the requests.
        url: URL of works with all filters.

    Returns:
        Source Model.

    Raises:
        httpx.HTTPStatusError: One response from OpenAlex API had an error HTTP status of 4xx or 5xx.
    """
    response = await client.get(url=url)
    response.raise_for_status()

    return Source(**response.json())


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
    author_profiles_keys = _get_author_profiles_keys(author, extra_profiles)
    profiles_query_parameter = "|".join(author_profiles_keys)

    pub_from_filter = f",from_publication_date:{pub_from_date:%Y-%m-%d}" if pub_from_date else ""
    pub_to_filter = f",to_publication_date:{pub_to_date:%Y-%m-%d}" if pub_to_date else ""
    url = (
        f"https://api.openalex.org/works?filter=author.id:{profiles_query_parameter}{pub_from_filter}{pub_to_filter}&sort=publication_date"
    )

    async with httpx.AsyncClient() as client:
        # Getting all the author works.
        author_works = await _get_works(client, url)

        # Extra filters
        cited_from_filter = f",from_publication_date:{cited_from_date:%Y-%m-%d}" if cited_from_date else ""
        cited_to_filter = f",to_publication_date:{cited_to_date:%Y-%m-%d}" if cited_to_date else ""

        # Report fields.
        works: list[WorkReport] = []
        report_citation_summary = CitationSummary()
        open_access_summary = OpenAccessSummary()
        works_type_counter: list[WorkTypeCounter] = []
        dehydrated_sources: list[DehydratedSource] = []

        # Getting all works that have cited the author.
        for author_work in author_works:
            work_id = identifier.get_work_id(author_work)
            work_authors = _get_authors_list(authorships=author_work.authorships)
            cited_by_api_url = (
                f"https://api.openalex.org/works?filter=cites:{work_id}{cited_from_filter}{cited_to_filter}&sort=publication_date"
            )

            # Adding the type of OpenAccess in the counter.
            open_access_summary.add_oa_type(author_work.open_access.oa_status)

            # Adding the work type to works type counter.
            work_type = next((work_type for work_type in works_type_counter if work_type.type_name == author_work.type), None)
            if work_type:
                work_type.count += 1
            else:
                works_type_counter.append(WorkTypeCounter(type_name=author_work.type, count=1))

            # Add Sources to global list.
            for location in author_work.locations:
                if location.source and not any(source.id == location.source.id for source in dehydrated_sources):
                    dehydrated_sources.append(location.source)

            cited_by_works = await _get_works(client, cited_by_api_url)
            cited_by: list[CitationReport] = []
            work_citation_summary = CitationSummary()
            for cited_by_work in cited_by_works:
                cited_authors = _get_authors_list(authorships=cited_by_work.authorships)
                citation_type = _get_citation_type(work_authors, cited_authors)

                # Adding the type of cites in the counters.
                report_citation_summary.add_cite_type(citation_type)
                work_citation_summary.add_cite_type(citation_type)

                cited_by.append(CitationReport(work=cited_by_work, citation_type=citation_type))

            works.append(WorkReport(work=author_work, cited_by=cited_by, citation_summary=work_citation_summary))

        # Get sources full info.
        sources: list[Source] = []
        for dehydrated_source in dehydrated_sources:
            source_id = identifier.get_source_id(dehydrated_source)
            source_url = f"https://api.openalex.org/sources/{source_id}"
            sources.append(await _get_source(client, source_url))

        # Sort sources by h_index
        sources_sorted = sorted(sources, key=lambda source: source.summary_stats.two_yr_mean_citedness, reverse=True)
        sources_summary = SourcesSummary(sources=sources_sorted)

    return AuthorReport(
        author=author,
        works=works,
        citation_summary=report_citation_summary,
        open_access_summary=open_access_summary,
        works_type_summary=works_type_counter,
        sources_summary=sources_summary,
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
    institution_keys = _get_institution_keys(institution, extra_profiles)
    institution_query_parameter = "|".join(institution_keys)

    pub_from_filter = f",from_publication_date:{pub_from_date:%Y-%m-%d}" if pub_from_date else ""
    pub_to_filter = f",to_publication_date:{pub_to_date:%Y-%m-%d}" if pub_to_date else ""
    url = f"https://api.openalex.org/works?filter=institutions.id:{institution_query_parameter}{pub_from_filter}{pub_to_filter}&sort=publication_date"

    async with httpx.AsyncClient() as client:
        # Getting all the institution works.
        institution_works = await _get_works(client=client, url=url)

        # Extra filters
        cited_from_filter = f",from_publication_date:{cited_from_date:%Y-%m-%d}" if cited_from_date else ""
        cited_to_filter = f",to_publication_date:{cited_to_date:%Y-%m-%d}" if cited_to_date else ""

        # Report fields.
        works: list[WorkReport] = []
        report_citation_summary = CitationSummary()
        open_access_summary = OpenAccessSummary()
        works_type_counter: list[WorkTypeCounter] = []
        dehydrated_sources: list[DehydratedSource] = []

        # Getting all works that have cited a work.
        for institution_work in institution_works:
            work_id = identifier.get_work_id(institution_work)
            work_authors = _get_authors_list(authorships=institution_work.authorships)
            cited_by_api_url = (
                f"https://api.openalex.org/works?filter=cites:{work_id}{cited_from_filter}{cited_to_filter}&sort=publication_date"
            )

            # Adding the type of OpenAccess in the counter.
            open_access_summary.add_oa_type(institution_work.open_access.oa_status)

            # Adding the work type to works type counter.
            work_type = next((work_type for work_type in works_type_counter if work_type.type_name == institution_work.type), None)
            if work_type:
                work_type.count += 1
            else:
                works_type_counter.append(WorkTypeCounter(type_name=institution_work.type, count=1))

            # Add Sources to global list.
            for location in institution_work.locations:
                if location.source and not any(source.id == location.source.id for source in dehydrated_sources):
                    dehydrated_sources.append(location.source)

            cited_by_works = await _get_works(client, cited_by_api_url)
            cited_by: list[CitationReport] = []
            work_citation_summary = CitationSummary()
            for cited_by_work in cited_by_works:
                cited_authors = _get_authors_list(authorships=cited_by_work.authorships)
                citation_type = _get_citation_type(work_authors, cited_authors)

                # Adding the type of cites in the counters.
                report_citation_summary.add_cite_type(citation_type)
                work_citation_summary.add_cite_type(citation_type)

                cited_by.append(CitationReport(work=cited_by_work, citation_type=citation_type))

            works.append(WorkReport(work=institution_work, cited_by=cited_by, citation_summary=work_citation_summary))

        # Get sources full info.
        sources: list[Source] = []
        for dehydrated_source in dehydrated_sources:
            source_id = identifier.get_source_id(dehydrated_source)
            source_url = f"https://api.openalex.org/sources/{source_id}"
            sources.append(await _get_source(client, source_url))

        # Sort sources by h_index
        sources_sorted = sorted(sources, key=lambda source: source.summary_stats.two_yr_mean_citedness, reverse=True)
        sources_summary = SourcesSummary(sources=sources_sorted)

    return InstitutionReport(
        institution=institution,
        works=works,
        citation_summary=report_citation_summary,
        open_access_summary=open_access_summary,
        works_type_summary=works_type_counter,
        sources_summary=sources_summary,
    )
