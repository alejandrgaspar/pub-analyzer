"""Test utils functions in pub_analyzer/utils/identifier.py."""

import pytest

from pub_analyzer.models.author import Author, AuthorResult, DehydratedAuthor
from pub_analyzer.utils.identifier import get_author_id, get_work_id
from tests.data.author import AUTHOR_OBJECT, AUTHOR_OPEN_ALEX_ID, AUTHOR_RESULT_OBJECT, DEHYDRATED_AUTHOR_OBJECT
from tests.data.work import WORK_OBJECT, WORK_OPEN_ALEX_ID


@pytest.mark.parametrize('model_input', [AUTHOR_OBJECT, AUTHOR_RESULT_OBJECT, DEHYDRATED_AUTHOR_OBJECT])
def test_get_author_id(model_input: Author | AuthorResult | DehydratedAuthor) -> None:
    """Test get_author_id function."""
    assert get_author_id(model_input) == AUTHOR_OPEN_ALEX_ID

def test_get_work_id() -> None:
    """Test get_work_if function."""
    assert get_work_id(WORK_OBJECT) == WORK_OPEN_ALEX_ID
