"""Functions to extract OpenAlex IDs from Models."""

from urllib.parse import urlsplit

from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionOpenAlexKey, InstitutionResult
from pub_analyzer.models.source import DehydratedSource, Source
from pub_analyzer.models.work import Work


def _get_key(openalex_id: str) -> str:
    """Extract the key, like `A000000000`, from an OpenAlex ID, like `https://openalex.org/A000000000`.

    Returns:
        Last segment of the path of the ID, or an empty string if it has no path.
    """
    return urlsplit(openalex_id).path.rpartition("/")[2]


def get_author_id(author: Author | AuthorResult | DehydratedAuthor) -> AuthorOpenAlexKey:
    """Extract OpenAlex ID from author Model.

    Args:
        author: Author model instance.

    Returns:
        Author OpenAlex ID.

    Example:
        ```python
        from pub_analyzer.internal.identifier import get_author_id
        from pub_analyzer.models.author import DehydratedAuthor

        author = DehydratedAuthor(id="https://openalex.org/A000000000")
        print(get_author_id(author))
        # 'A000000000'
        ```
    """
    return _get_key(author.id)


def get_institution_id(institution: Institution | InstitutionResult | DehydratedInstitution) -> InstitutionOpenAlexKey:
    """Extract OpenAlex ID from institution Model.

    Args:
        institution: Institution model instance.

    Returns:
        Institution OpenAlex ID.

    Example:
        ```python
        from pub_analyzer.internal.identifier import get_institution_id
        from pub_analyzer.models.institution import DehydratedInstitution

        institution = DehydratedInstitution(id="https://openalex.org/I000000000", **kwargs)
        print(get_institution_id(institution))
        # 'I000000000'
        ```
    """
    return _get_key(institution.id)


def get_work_id(work: Work) -> str:
    """Extract OpenAlex ID from Work Model.

    Args:
        work: Work model instance.

    Returns:
        Work OpenAlex ID.

    Example:
        ```python
        from pub_analyzer.internal.identifier import get_work_id
        from pub_analyzer.models.work import Work

        work = Work(id="https://openalex.org/W000000000", **kwargs)
        print(get_work_id(work))
        # 'W000000000'
        ```
    """
    return _get_key(work.id)


def get_source_id(source: DehydratedSource | Source) -> str:
    """Extract OpenAlex ID from Source Model.

    Args:
        source: Source model instance.

    Returns:
        Source OpenAlex ID.

    Example:
        ```python
        from pub_analyzer.internal.identifier import get_source_id
        from pub_analyzer.models.source import Source

        source = Source(id="https://openalex.org/S000000000", **kwargs)
        print(get_source_id(source))
        # 'S000000000'
        ```
    """
    return _get_key(source.id)
