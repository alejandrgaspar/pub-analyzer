"""Test functions from pub_analyzer/internal/identifier.py."""

import pytest

from pub_analyzer.internal.identifier import get_author_id, get_institution_id, get_source_id, get_work_id
from pub_analyzer.models.author import Author, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionResult
from pub_analyzer.models.source import DehydratedSource, Source
from tests.data.author import AUTHOR_OBJECT, AUTHOR_OPEN_ALEX_ID, AUTHOR_RESULT_OBJECT, DEHYDRATED_AUTHOR_OBJECT
from tests.data.institution import DEHYDRATED_INSTITUTION_OBJECT, INSTITUTION_OBJECT, INSTITUTION_OPEN_ALEX_ID, INSTITUTION_RESULT_OBJECT
from tests.data.source import DEHYDRATED_SOURCE_OBJECT, SOURCE_OBJECT, SOURCE_OPEN_ALEX_ID
from tests.data.work import WORK_OBJECT, WORK_OPEN_ALEX_ID


@pytest.mark.parametrize("model_input", [AUTHOR_OBJECT, AUTHOR_RESULT_OBJECT, DEHYDRATED_AUTHOR_OBJECT])
def test_get_author_id(model_input: Author | AuthorResult | DehydratedAuthor) -> None:
    """Test get_author_id function."""
    assert get_author_id(model_input) == AUTHOR_OPEN_ALEX_ID


@pytest.mark.parametrize("model_input", [INSTITUTION_OBJECT, INSTITUTION_RESULT_OBJECT, DEHYDRATED_INSTITUTION_OBJECT])
def test_get_institution_id(model_input: Institution | InstitutionResult | DehydratedInstitution) -> None:
    """Test get_institution_id function."""
    assert get_institution_id(model_input) == INSTITUTION_OPEN_ALEX_ID


def test_get_work_id() -> None:
    """Test get_work_id function."""
    assert get_work_id(WORK_OBJECT) == WORK_OPEN_ALEX_ID


@pytest.mark.parametrize("model_input", [SOURCE_OBJECT, DEHYDRATED_SOURCE_OBJECT])
def test_get_source_id(model_input: Source | DehydratedSource) -> None:
    """Test get_institution_id function."""
    assert get_source_id(model_input) == SOURCE_OPEN_ALEX_ID
