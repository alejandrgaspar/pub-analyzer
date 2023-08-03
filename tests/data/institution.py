"""
Institution model sample data.

Information of University of Colima.
https://www.ucol.mx/
"""

from typing import Any

from pub_analyzer.models.institution import InstitutionResult

INSTITUTION_OPEN_ALEX_ID = "I916541031"
OPEN_ALEX_ID_URL = "https://openalex.org/" + INSTITUTION_OPEN_ALEX_ID
DISPLAY_NAME = "University of Colima"


INSTITUTION_RESULT: dict[str, Any] = {
    "id": OPEN_ALEX_ID_URL,
    "display_name": DISPLAY_NAME,
    "hint": "Colima, Mexico",
    "cited_by_count": 40292,
    "works_count": 5347,
    "entity_type": "institution",
    "external_id": "https://ror.org/04znxe670"
}


INSTITUTION_RESULT_OBJECT = InstitutionResult(**INSTITUTION_RESULT)
