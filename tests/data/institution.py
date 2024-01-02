"""
Institution model sample data.

Information of University of Colima.
https://www.ucol.mx/
"""

from typing import Any

from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionResult

INSTITUTION_OPEN_ALEX_ID = "I916541031"
OPEN_ALEX_ID_URL = "https://openalex.org/" + INSTITUTION_OPEN_ALEX_ID
DISPLAY_NAME = "University of Colima"


INSTITUTION: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "ids": {
        "openalex": OPEN_ALEX_ID_URL,
        "ror": "https://ror.org/04znxe670",
        "mag": "916541031",
        "grid": "grid.412887.0",
        "wikipedia": "https://en.wikipedia.org/wiki/University%20of%20Colima",
        "wikidata": "https://www.wikidata.org/wiki/Q2495731",
    },
    "display_name": DISPLAY_NAME,
    "country_code": "MX",
    "type": "education",
    "homepage_url": "http://www.ucol.mx/",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/7d/Logo_de_la_Universidad_de_Colima.svg",
    "display_name_acronyms": [],
    "international": {
        "display_name": {
            "ca": "Universitat de Colima",
            "cy": "Prifysgol Colima",
            "de": "Universidad de Colima",
            "en": "University of Colima",
            "es": "Universidad de Colima",
            "fr": "université de Colima",
            "ga": "Ollscoil Colima",
            "it": "Università de Colima",
            "nl": "University of Colima",
            "zh": "科利马大学",
            "zh-cn": "科利马大学",
            "zh-hans": "科利马大学",
            "zh-hant": "科利馬大學",
        }
    },
    "works_count": 5347,
    "cited_by_count": 40292,
    "counts_by_year": [
        {"year": 2023, "works_count": 188, "cited_by_count": 3525},
        {"year": 2022, "works_count": 341, "cited_by_count": 5876},
        {"year": 2021, "works_count": 354, "cited_by_count": 5267},
    ],
    "summary_stats": {"2yr_mean_citedness": 2.366178428761651, "h_index": 78, "i10_index": 959},
    "geo": {
        "city": "Colima",
        "geonames_city_id": "4013516",
        "region": None,
        "country_code": "MX",
        "country": "Mexico",
        "latitude": 19.265818,
        "longitude": -103.74164,
    },
    "roles": [
        {"role": "publisher", "id": "https://openalex.org/P4310319647", "works_count": 1164},
        {"role": "institution", "id": "https://openalex.org/I916541031", "works_count": 5347},
        {"role": "funder", "id": "https://openalex.org/F4320318845", "works_count": 3},
    ],
    "repositories": [],
    "works_api_url": "https://api.openalex.org/works?filter=institutions.id:I916541031",
}

INSTITUTION_RESULT: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "display_name": DISPLAY_NAME,
    "hint": "Colima, Mexico",
    "cited_by_count": 40292,
    "works_count": 5347,
    "entity_type": "institution",
    "external_id": "https://ror.org/04znxe670",
}

DEHYDRATED_INSTITUTION: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "ror": "https://ror.org/04znxe670",
    "display_name": DISPLAY_NAME,
    "country_code": "MX",
    "type": "education",
}


INSTITUTION_OBJECT = Institution(**INSTITUTION)
INSTITUTION_RESULT_OBJECT = InstitutionResult(**INSTITUTION_RESULT)
DEHYDRATED_INSTITUTION_OBJECT = DehydratedInstitution(**DEHYDRATED_INSTITUTION)
