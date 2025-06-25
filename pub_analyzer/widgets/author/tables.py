"""Author Tables Widgets."""

from urllib.parse import quote

from rich.table import Table
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.author import Author


class AuthorWorksByYearTable(Static):
    """Table with Work count and cited by count of the last 10 years."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        table = Table("Year", "Works Count", "Cited by Count", title="Counts by Year", expand=True)
        for row in self.author.counts_by_year:
            year, works_count, cited_by_count = row.model_dump().values()
            table.add_row(str(year), str(works_count), str(cited_by_count))

        yield Static(table)


class AffiliationsTable(Static):
    """Table with all the institutions to which an author has been affiliated."""

    def __init__(self, author: Author) -> None:
        self.author = author
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        table = Table("Institution", "Country", "Type", "Years", title="Affiliations", expand=True, show_lines=True)
        for affiliation in self.author.affiliations:
            institution = affiliation.institution
            institution_name = (
                f"""[@click=app.open_link("{quote(str(institution.ror))}")]{institution.display_name}[/]"""
                if institution.ror
                else f"{institution.display_name}"
            )
            years = ",".join([str(year) for year in affiliation.years])
            country_code = institution.country_code.upper() if institution.country_code else "-"
            table.add_row(str(institution_name), str(country_code), str(institution.type.name), str(years))

        yield Static(table)
