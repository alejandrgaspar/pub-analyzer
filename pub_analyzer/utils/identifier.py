"""Extract Ids Utils."""

from pub_analyzer.models.work import Author, WorkInfo


def get_author_id(author: Author) -> str:
    """Extract OpenAlex ID from Author Model."""
    if author.id.path:
        return author.id.path.rpartition('/')[2]
    else:
        return ''

def get_work_id(work: WorkInfo) -> str:
    """Extract OpenAlex ID from Work Model."""
    if work.id.path:
        return work.id.path.rpartition('/')[2]
    else:
        return ''
