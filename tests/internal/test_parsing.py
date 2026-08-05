"""Test payload normalization from pub_analyzer/internal/openalex/parsing.py."""

from typing import Any

import pytest

from pub_analyzer.internal.openalex import parsing


@pytest.mark.parametrize(
    ["inverted_index", "expected_abstract"],
    [
        pytest.param(
            {"Fear": [0], "is": [1], "the": [2], "mind-killer.": [3]},
            "Fear is the mind-killer.",
            id="already-ordered",
        ),
        pytest.param(
            {"mind-killer.": [3], "the": [2], "Fear": [0], "is": [1]},
            "Fear is the mind-killer.",
            id="keys-out-of-order",
        ),
        pytest.param(
            {"the": [0, 2], "cat": [1], "hat": [3]},
            "the cat the hat",
            id="repeated-word-kept-at-every-position",
        ),
        pytest.param(
            {"one": [0]},
            "one",
            id="single-word",
        ),
        pytest.param(None, None, id="missing"),
        pytest.param({}, None, id="empty"),
    ],
)
def test_reconstruct_abstract(inverted_index: dict[str, list[int]] | None, expected_abstract: str | None) -> None:
    """Test reconstruct_abstract function."""
    assert parsing.reconstruct_abstract(inverted_index) == expected_abstract


def test_reconstruct_abstract_keeps_every_occurrence() -> None:
    """Every position in the index must appear in the abstract."""
    inverted_index = {"a": [0, 2, 4], "b": [1, 5], "c": [3]}

    abstract = parsing.reconstruct_abstract(inverted_index)

    assert abstract == "a b a c a b"
    assert abstract is not None
    assert len(abstract.split()) == sum(len(positions) for positions in inverted_index.values())


@pytest.mark.parametrize(
    ["work", "expected_abstract"],
    [
        [{"abstract_inverted_index": {"Fear": [0], "is": [1], "the": [2], "mind-killer.": [3]}}, "Fear is the mind-killer."],
        [{"abstract_inverted_index": None}, None],
        [{}, None],
    ],
)
def test_add_work_abstract(work: dict[str, Any], expected_abstract: str | None) -> None:
    """Test add_work_abstract function."""
    assert parsing.add_work_abstract(work)["abstract"] == expected_abstract


@pytest.mark.parametrize(
    ["works", "expected_works"],
    [
        [
            [
                {"id": "W4356881717", "title": "Title1", "language": "en"},
                {"id": "W2058179313", "title": "Title2", "language": None},
                {"id": "W1956475281", "title": None, "language": "es"},
            ],
            [
                {"id": "W4356881717", "title": "Title1", "language": "en", "abstract": None},
                {"id": "W2058179313", "title": "Title2", "language": None, "abstract": None},
            ],
        ],
        [[], []],
    ],
)
def test_get_valid_works(works: list[dict[str, Any]], expected_works: list[dict[str, Any]]) -> None:
    """Test get_valid_works function."""
    assert parsing.get_valid_works(works) == expected_works
