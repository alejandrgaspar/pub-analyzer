"""Functions to extract OpenAlex IDs from Models."""

from pub_analyzer.models.author import Author, AuthorOpenAlexKey, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution, InstitutionOpenAlexKey, InstitutionResult
from pub_analyzer.models.work import Work


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
    if author.id.path:
        return author.id.path.rpartition('/')[2]
    else:
        return ''


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
    if institution.id.path:
        return institution.id.path.rpartition('/')[2]
    else:
        return ''


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
    if work.id.path:
        return work.id.path.rpartition('/')[2]
    else:
        return ''
