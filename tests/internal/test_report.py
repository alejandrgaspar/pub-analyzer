"""Test builder functions from pub_analyzer/internal/report/builder.py."""

import pytest
from pydantic import HttpUrl

from pub_analyzer.internal.report import builder
from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionOpenAlexKey, InstitutionResult, InstitutionType


def _dehydrated_institution(institution_id: str) -> DehydratedInstitution:
    """Build a DehydratedInstitution from a bare OpenAlex key."""
    return DehydratedInstitution(
        id=HttpUrl(f"https://openalex.org/{institution_id}"),
        ror="",
        display_name="",
        country_code="",
        type=InstitutionType.Education,
    )


@pytest.mark.parametrize(
    ["main_author", "extra_profiles", "expected_keys"],
    [
        pytest.param(DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")), None, ["A0"], id="no-extra-profiles"),
        pytest.param(DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")), [], ["A0"], id="empty-extra-profiles"),
        pytest.param(
            DehydratedAuthor(id=HttpUrl("https://openalex.org/A0")),
            [
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A1")),
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A2")),
                DehydratedAuthor(id=HttpUrl("https://openalex.org/A3")),
            ],
            ["A0", "A1", "A2", "A3"],
            id="with-extra-profiles",
        ),
    ],
)
def test_get_author_profiles_keys(
    main_author: Author, extra_profiles: list[Author | AuthorResult | DehydratedAuthor] | None, expected_keys: list[AuthorOpenAlexKey]
) -> None:
    """Test _get_author_profiles_keys function."""
    assert builder._get_author_profiles_keys(main_author, extra_profiles) == expected_keys


@pytest.mark.parametrize(
    ["main_institution", "extra_profiles", "expected_keys"],
    [
        pytest.param(_dehydrated_institution("I0"), None, ["I0"], id="no-extra-profiles"),
        pytest.param(_dehydrated_institution("I0"), [], ["I0"], id="empty-extra-profiles"),
        pytest.param(
            _dehydrated_institution("I0"),
            [_dehydrated_institution("I1"), _dehydrated_institution("I2"), _dehydrated_institution("I3")],
            ["I0", "I1", "I2", "I3"],
            id="with-extra-profiles",
        ),
    ],
)
def test_get_institution_keys(
    main_institution: Institution,
    extra_profiles: list[Institution | InstitutionResult | DehydratedInstitution] | None,
    expected_keys: list[InstitutionOpenAlexKey],
) -> None:
    """Test _get_institution_keys function."""
    assert builder._get_institution_keys(main_institution, extra_profiles) == expected_keys
