"""Source model sample data."""

from typing import Any

from pub_analyzer.models.source import DehydratedSource, Source

SOURCE_OPEN_ALEX_ID = "S137773608"
OPEN_ALEX_ID_URL = "https://openalex.org/" + SOURCE_OPEN_ALEX_ID
DISPLAY_NAME = "University of Colima"

SOURCE: dict[str, Any] = {
    "id": "https://openalex.org/S137773608",
    "issn_l": "0028-0836",
    "issn": ["1476-4687", "0028-0836"],
    "display_name": "Nature",
    "host_organization": "https://openalex.org/P4310319908",
    "host_organization_name": "Nature Portfolio",
    "host_organization_lineage": ["https://openalex.org/P4310319908", "https://openalex.org/P4310319965"],
    "works_count": 431710,
    "cited_by_count": 21796015,
    "summary_stats": {"2yr_mean_citedness": 16.19942269076305, "h_index": 1639, "i10_index": 106155},
    "is_oa": False,
    "is_in_doaj": False,
    "ids": {
        "openalex": "https://openalex.org/S137773608",
        "issn_l": "0028-0836",
        "issn": ["1476-4687", "0028-0836"],
        "mag": "137773608",
        "wikidata": "https://www.wikidata.org/entity/Q180445",
    },
    "homepage_url": "https://www.nature.com/nature/",
    "apc_prices": [{"price": 9750, "currency": "EUR"}, {"price": 11690, "currency": "USD"}, {"price": 8490, "currency": "GBP"}],
    "apc_usd": 11690,
    "country_code": "GB",
    "societies": [],
    "alternate_titles": [],
    "abbreviated_title": None,
    "type": "journal",
    "x_concepts": [
        {
            "id": "https://openalex.org/C86803240",
            "wikidata": "https://www.wikidata.org/wiki/Q420",
            "display_name": "Biology",
            "level": 0,
            "score": 57.3,
        },
        {
            "id": "https://openalex.org/C121332964",
            "wikidata": "https://www.wikidata.org/wiki/Q413",
            "display_name": "Physics",
            "level": 0,
            "score": 39.3,
        },
        {
            "id": "https://openalex.org/C185592680",
            "wikidata": "https://www.wikidata.org/wiki/Q2329",
            "display_name": "Chemistry",
            "level": 0,
            "score": 35.8,
        },
    ],
    "counts_by_year": [
        {"year": 2024, "works_count": 215, "cited_by_count": 81785},
        {"year": 2023, "works_count": 4308, "cited_by_count": 1102943},
        {"year": 2022, "works_count": 4102, "cited_by_count": 1155839},
        {"year": 2021, "works_count": 3757, "cited_by_count": 1186348},
        {"year": 2020, "works_count": 3606, "cited_by_count": 1082409},
        {"year": 2019, "works_count": 4035, "cited_by_count": 957044},
        {"year": 2018, "works_count": 4033, "cited_by_count": 907338},
        {"year": 2017, "works_count": 3901, "cited_by_count": 844085},
        {"year": 2016, "works_count": 4140, "cited_by_count": 823447},
        {"year": 2015, "works_count": 4240, "cited_by_count": 810154},
        {"year": 2014, "works_count": 4133, "cited_by_count": 802687},
        {"year": 2013, "works_count": 4225, "cited_by_count": 781477},
        {"year": 2012, "works_count": 4342, "cited_by_count": 728040},
    ],
    "works_api_url": "https://api.openalex.org/works?filter=primary_location.source.id:S137773608",
}

DEHYDRATED_SOURCE: dict[str, Any] = {
    "id": "https://openalex.org/S137773608",
    "display_name": "Nature",
    "issn_l": "0028-0836",
    "issn": ["1476-4687", "0028-0836"],
    "is_oa": False,
    "is_in_doaj": False,
    "host_organization": "https://openalex.org/P4310319908",
    "host_organization_name": "Nature Portfolio",
    "host_organization_lineage": ["https://openalex.org/P4310319908", "https://openalex.org/P4310319965"],
    "host_organization_lineage_names": ["Nature Portfolio", "Springer Nature"],
    "type": "journal",
}


SOURCE_OBJECT = Source(**SOURCE)
DEHYDRATED_SOURCE_OBJECT = DehydratedSource(**DEHYDRATED_SOURCE)
