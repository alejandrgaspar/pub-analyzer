"""Institution Tables Widgets."""

from rich.table import Table
from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.models.institution import Institution


class InstitutionWorksByYearTable(Static):
    """Table with Work count and cited by count of the last 10 years."""

    def __init__(self, institution: Institution) -> None:
        self.institution = institution
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        table = Table('Year', 'Works Count', 'Cited by Count', title="Counts by Year", expand=True)
        for row in self.institution.counts_by_year:
            year, works_count, cited_by_count = row.model_dump().values()
            table.add_row(str(year), str(works_count), str(cited_by_count))

        yield Static(table)
