"""Functions to make author reports."""

import math
from urllib.parse import urlparse

import httpx
from pydantic import parse_obj_as

from pub_analyzer.models.report import CitationReport, CitationType, Report, WorkReport
from pub_analyzer.models.researcher import ResearcherExtendedInfo
from pub_analyzer.models.work import Authorship, WorkInfo


def _get_authors_list(authorships: list[Authorship]) -> list[str]:
    """Collect OpenAlex IDs from authors in a list."""
    return [urlparse(authorship.author.id).path.rpartition('/')[2] for authorship in authorships]


def _get_citation_type(original_work_authors: list[str], cited_work_authors: list[str]) -> CitationType:
    """Compare two lists of authors and returns the citation type."""
    original_set = set(original_work_authors)
    cited_set = set(cited_work_authors)

    return CitationType.TypeA if not original_set.intersection(cited_set) else CitationType.TypeB


async def _get_works(client: httpx.AsyncClient, url: str) -> list[WorkInfo]:
    """Pass."""
    response = (await client.get(url=url)).json()
    meta_info = response["meta"]
    page_count = math.ceil(meta_info["count"] / meta_info["per_page"])

    works_data = list(response["results"],)

    for page_number in range(1, page_count):
        page_result = (await client.get(url + f"?page={page_number + 1}")).json()
        works_data.extend(page_result["results"])

    return parse_obj_as(list[WorkInfo], works_data)


async def make_report(author: ResearcherExtendedInfo) -> Report:
    """Make a citation report using an Author's OpenAlex ID."""
    author_id = urlparse(author.id).path.rpartition('/')[2]
    url = f"https://api.openalex.org/works?filter=author.id:{author_id}"

    async with httpx.AsyncClient() as client:
        # Getting all the author's works.
        author_works = await _get_works(client, url)

        # Getting all works that have cited the author.
        works: list[WorkReport] = []
        for author_work in author_works:
            work_id = urlparse(author_work.id).path.rpartition('/')[2]
            work_authors = _get_authors_list(authorships=author_work.authorships)
            cited_by_api_url = f"https://api.openalex.org/works?filter=cites:{work_id}"

            cited_by_works = await _get_works(client, cited_by_api_url)

            cited_by: list[CitationReport] = []
            for cited_by_work in cited_by_works:
                cited_authors = _get_authors_list(authorships=cited_by_work.authorships)
                citation_type = _get_citation_type(work_authors, cited_authors)

                cited_by.append(CitationReport(work=cited_by_work, citation_type=citation_type))

            works.append(WorkReport(work=author_work, cited_by=cited_by))

    return Report(author=author, works=works)
