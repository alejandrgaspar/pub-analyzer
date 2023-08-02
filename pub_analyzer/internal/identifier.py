"""Extract Ids functions."""

from pub_analyzer.models.author import Author, AuthorResult, DehydratedAuthor
from pub_analyzer.models.institution import DehydratedInstitution, Institution
from pub_analyzer.models.work import Work


def get_author_id(author: Author | AuthorResult | DehydratedAuthor) -> str:
    """Extract OpenAlex ID from Author Model."""
    if author.id.path:
        return author.id.path.rpartition('/')[2]
    else:
        return ''


def get_institution_id(institution: Institution | DehydratedInstitution) -> str:
    """Extract OpenAlex ID from Author Model."""
    if institution.id.path:
        return institution.id.path.rpartition('/')[2]
    else:
        return ''


def get_work_id(work: Work) -> str:
    """Extract OpenAlex ID from Work Model."""
    if work.id.path:
        return work.id.path.rpartition('/')[2]
    else:
        return ''
