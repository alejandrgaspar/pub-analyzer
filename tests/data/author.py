"""
Author model sample data.

Information of Mario J. Molina, Nobel Prize Winning Mexican Chemist.
https://en.wikipedia.org/wiki/Mario_Molina
"""

from typing import Any

from pub_analyzer.models.author import Author, AuthorResult, DehydratedAuthor

AUTHOR_OPEN_ALEX_ID = "A5090292188"
OPEN_ALEX_ID_URL = "https://openalex.org/" + AUTHOR_OPEN_ALEX_ID
DISPLAY_NAME = "Mario J. Molina"
ORCID = None

AUTHOR: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "orcid": ORCID,
    "display_name": DISPLAY_NAME,
    "display_name_alternatives": [],
    "works_count": 185,
    "cited_by_count": 19275,
    "summary_stats": {
        "2yr_mean_citedness": 37.375,
        "h_index": 57,
        "i10_index": 125
    },
    "ids": {
        "openalex": OPEN_ALEX_ID_URL
    },
    "last_known_institution": {
        "id": "https://openalex.org/I36258959",
        "ror": "https://ror.org/0168r3w48",
        "display_name": "University of California, San Diego",
        "country_code": "US",
        "type": "education"
    },
    "counts_by_year": [
        {
            "year": 2023,
            "works_count": 0,
            "cited_by_count": 914
        },
        {
            "year": 2022,
            "works_count": 0,
            "cited_by_count": 1894
        },
        {
            "year": 2021,
            "works_count": 1,
            "cited_by_count": 2361
        }
    ],
    "works_api_url": "https://api.openalex.org/works?filter=author.id:A4356881717"
}

AUTHOR_RESULT: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "display_name": DISPLAY_NAME,
    "hint": "University of California, San Diego, USA",
    "cited_by_count": 19275,
    "works_count": 185,
    "entity_type": "author",
    "external_id": None,
    "filter_key": None
}

DEHYDRATED_AUTHOR: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "display_name": DISPLAY_NAME,
    "orcid": ORCID
}


AUTHOR_OBJECT = Author(**AUTHOR)
AUTHOR_RESULT_OBJECT = AuthorResult(**AUTHOR_RESULT)
DEHYDRATED_AUTHOR_OBJECT = DehydratedAuthor(**DEHYDRATED_AUTHOR)
