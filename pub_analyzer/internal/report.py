"""Functions to make reports."""

import math
from typing import Any

import httpx
from pydantic import TypeAdapter

from pub_analyzer.internal import identifier
from pub_analyzer.models.author import Author
from pub_analyzer.models.institution import Institution
from pub_analyzer.models.report import (
    AuthorReport,
    CitationReport,
    CitationResume,
    CitationType,
    InstitutionReport,
    OpenAccessResume,
    SourcesResume,
    WorkReport,
    WorkTypeCounter,
)
from pub_analyzer.models.work import Authorship, Work


def _get_authors_list(authorships: list[Authorship]) -> list[str]:
    """Collect OpenAlex IDs from authors in a list."""
    return [identifier.get_author_id(authorship.author) for authorship in authorships]


def _get_citation_type(original_work_authors: list[str], cited_work_authors: list[str]) -> CitationType:
    """Compare two lists of authors and returns the citation type."""
    original_set = set(original_work_authors)
    cited_set = set(cited_work_authors)

    return CitationType.TypeA if not original_set.intersection(cited_set) else CitationType.TypeB

def _get_valid_works(works: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Skip works that do not contain enough data."""
    return [work for work in works if work['title'] is not None]

async def _get_works(client: httpx.AsyncClient, url: str) -> list[Work]:
    """Pass."""
    response = (await client.get(url=url)).json()
    meta_info = response["meta"]
    page_count = math.ceil(meta_info["count"] / meta_info["per_page"])

    works_data = list(_get_valid_works(response["results"]),)

    for page_number in range(1, page_count):
        page_result = (await client.get(url + f"&page={page_number + 1}")).json()
        works_data.extend(_get_valid_works(page_result["results"]))

    return TypeAdapter(list[Work]).validate_python(works_data)


async def make_author_report(author: Author) -> AuthorReport:
    """Make a scientific production report by Author."""
    author_id = identifier.get_author_id(author)
    url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_date"

    async with httpx.AsyncClient() as client:
        # Getting all the author works.
        author_works = await _get_works(client, url)

        # Report fields.
        works: list[WorkReport] = []
        report_citation_resume = CitationResume()
        open_access_resume = OpenAccessResume()
        works_type_counter: list[WorkTypeCounter] = []
        sources_resume = SourcesResume(sources=[])

        # Getting all works that have cited the author.
        for author_work in author_works:
            work_id = identifier.get_work_id(author_work)
            work_authors = _get_authors_list(authorships=author_work.authorships)
            cited_by_api_url = f"https://api.openalex.org/works?filter=cites:{work_id}&sort=publication_date"

            # Adding the type of OpenAccess in the counter.
            open_access_resume.add_oa_type(author_work.open_access.oa_status)

            # Adding the work type to works type counter.
            work_type = next((work_type for work_type in works_type_counter if work_type.type_name == author_work.type), None)
            if work_type:
                work_type.count += 1
            else:
                works_type_counter.append(WorkTypeCounter(type_name=author_work.type, count=1))

            # Add Sources to global list.
            for location in author_work.locations:
                if location.source and not any(source.display_name == location.source.display_name for source in sources_resume.sources):
                    sources_resume.sources.append(location.source)

            cited_by_works = await _get_works(client, cited_by_api_url)
            cited_by: list[CitationReport] = []
            work_citation_resume = CitationResume()
            for cited_by_work in cited_by_works:
                cited_authors = _get_authors_list(authorships=cited_by_work.authorships)
                citation_type = _get_citation_type(work_authors, cited_authors)

                # Adding the type of cites in the counters.
                report_citation_resume.add_cite_type(citation_type)
                work_citation_resume.add_cite_type(citation_type)

                cited_by.append(CitationReport(work=cited_by_work, citation_type=citation_type))

            works.append(WorkReport(work=author_work, cited_by=cited_by, citation_resume=work_citation_resume))

    return AuthorReport(
        author=author,
        works=works,
        citation_resume=report_citation_resume,
        open_access_resume=open_access_resume,
        works_type_resume=works_type_counter,
        sources_resume=sources_resume
    )


async def make_institution_report(institution: Institution) -> InstitutionReport:
    """Make a scientific production report by Institution."""
    institution_id = identifier.get_institution_id(institution)
    url = f"https://api.openalex.org/works?filter=institutions.id:{institution_id}&sort=publication_date"

    async with httpx.AsyncClient() as client:
        # Getting all the institution works.
        institution_works = await _get_works(client=client, url=url)

        # Report fields.
        works: list[WorkReport] = []
        report_citation_resume = CitationResume()
        open_access_resume = OpenAccessResume()
        works_type_counter: list[WorkTypeCounter] = []
        sources_resume = SourcesResume(sources=[])

        # Getting all works that have cited a work.
        for institution_work in institution_works:
            work_id = identifier.get_work_id(institution_work)
            work_authors = _get_authors_list(authorships=institution_work.authorships)
            cited_by_api_url = f"https://api.openalex.org/works?filter=cites:{work_id}&sort=publication_date"

            # Adding the type of OpenAccess in the counter.
            open_access_resume.add_oa_type(institution_work.open_access.oa_status)

            # Adding the work type to works type counter.
            work_type = next((work_type for work_type in works_type_counter if work_type.type_name == institution_work.type), None)
            if work_type:
                work_type.count += 1
            else:
                works_type_counter.append(WorkTypeCounter(type_name=institution_work.type, count=1))

            # Add Sources to global list.
            for location in institution_work.locations:
                if location.source and not any(source.display_name == location.source.display_name for source in sources_resume.sources):
                    sources_resume.sources.append(location.source)

            cited_by_works = await _get_works(client, cited_by_api_url)
            cited_by: list[CitationReport] = []
            work_citation_resume = CitationResume()
            for cited_by_work in cited_by_works:
                cited_authors = _get_authors_list(authorships=cited_by_work.authorships)
                citation_type = _get_citation_type(work_authors, cited_authors)

                # Adding the type of cites in the counters.
                report_citation_resume.add_cite_type(citation_type)
                work_citation_resume.add_cite_type(citation_type)

                cited_by.append(CitationReport(work=cited_by_work, citation_type=citation_type))

            works.append(WorkReport(work=institution_work, cited_by=cited_by, citation_resume=work_citation_resume))

    return InstitutionReport(
        works=works,
        citation_resume=report_citation_resume,
        open_access_resume=open_access_resume,
        works_type_resume=works_type_counter,
        sources_resume=sources_resume
    )