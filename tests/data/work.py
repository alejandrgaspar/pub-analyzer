"""
Work model sample data.

Information of Mario J. Molina, Nobel Prize Winning Mexican Chemist.
https://en.wikipedia.org/wiki/Mario_Molina
"""

from typing import Any

from pub_analyzer.models.work import Work

WORK_OPEN_ALEX_ID = "W2058179313"

WORK: dict[str, Any] = {
    "id": "https://openalex.org/" + WORK_OPEN_ALEX_ID,
    "title": "Stratospheric sink for chlorofluoromethanes: chlorine atom-catalysed destruction of ozone",
    "publication_year": 1974,
    "publication_date": "1974-06-01",
    "ids": {
        "openalex": "https://openalex.org/" + WORK_OPEN_ALEX_ID,
        "doi": "https://doi.org/10.1038/249810a0",
        "mag": "2058179313"
    },
    "language": "en",
    "primary_location": {
        "is_oa": False,
        "landing_page_url": "https://doi.org/10.1038/249810a0",
        "pdf_url": None,
        "license": None,
        "version": None
    },
    "type": "journal-article",
    "open_access": {
        "is_oa": False,
        "oa_status": "closed",
        "oa_url": None,
        "any_repository_has_fulltext": False
    },
    "authorships": [
        {
            "author_position": "first",
            "author": {
                "id": "https://openalex.org/A4356881717",
                "display_name": "Mario J. Molina",
                "orcid": None
            }
        },
        {
            "author_position": "last",
            "author": {
                "id": "https://openalex.org/A4346008987",
                "display_name": "F. Sherwood Rowland",
                "orcid": None
            }
        }
    ],
    "cited_by_count": 3700,
    "referenced_works_count": 21,
    "referenced_works": [
        "https://openalex.org/W1956475281",
        "https://openalex.org/W1973329720",
        "https://openalex.org/W1973392759",
        "https://openalex.org/W1975316895",
        "https://openalex.org/W1980980829",
        "https://openalex.org/W2009846251",
        "https://openalex.org/W2011611720",
        "https://openalex.org/W2022351337",
        "https://openalex.org/W2033446159",
        "https://openalex.org/W2034420907",
        "https://openalex.org/W2055873026",
        "https://openalex.org/W2059837773",
        "https://openalex.org/W2069552753",
        "https://openalex.org/W2073497703",
        "https://openalex.org/W2076193661",
        "https://openalex.org/W2084374407",
        "https://openalex.org/W2090510976",
        "https://openalex.org/W2127703393",
        "https://openalex.org/W2164314714",
        "https://openalex.org/W2326876406",
        "https://openalex.org/W2793356690"
    ],
    "cited_by_api_url": "https://api.openalex.org/works?filter=cites:" + WORK_OPEN_ALEX_ID,
}

WORK_OBJECT = Work(**WORK)