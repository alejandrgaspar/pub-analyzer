"""Normalization of raw OpenAlex payloads, applied before Model validation."""

from collections.abc import Mapping
from typing import Any

from textual import log


def reconstruct_abstract(abstract_inverted_index: Mapping[str, list[int]] | None) -> str | None:
    """Rebuild an abstract from the inverted index OpenAlex publishes.

    OpenAlex stores abstracts as a mapping of word to the positions that word takes
    in the text. Rebuilding means placing every word back at each of its positions.

    Args:
        abstract_inverted_index: Mapping of word to its positions in the abstract.

    Returns:
        The abstract, or `None` when the work has no abstract.

    Example:
        ```python
        reconstruct_abstract({"the": [0, 2], "cat": [1], "hat": [3]})
        # 'the cat the hat'
        ```
    """
    if not abstract_inverted_index:
        return None

    words_by_position = sorted((position, word) for word, positions in abstract_inverted_index.items() for position in positions)

    return " ".join(word for _, word in words_by_position)


def add_work_abstract(work: dict[str, Any]) -> dict[str, Any]:
    """Insert the rebuilt `abstract` key into a raw work.

    Args:
        work: Raw work.

    Returns:
        Work with new key `abstract`.
    """
    work["abstract"] = reconstruct_abstract(work.get("abstract_inverted_index"))
    return work


def get_valid_works(works: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Skip works that do not contain enough data.

    Args:
        works: List of raw works.

    Returns:
        List of raw works with enough data to pass the Works validation.

    Danger:
        Sometimes OpenAlex provides works with insufficient information to be considered.
        In response, we have chosen to exclude such works at this stage, thus avoiding
        the need to handle exceptions within the Model validators.
    """
    valid_works = []
    for work in works:
        if work["title"] is not None:
            valid_works.append(add_work_abstract(work))
        else:
            log.warning(f"Discarded work: {work['id']}")

    return valid_works
