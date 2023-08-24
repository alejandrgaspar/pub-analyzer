"""Render reports."""

import pathlib
from importlib.metadata import version

import typst
from jinja2 import Environment, FileSystemLoader

from pub_analyzer.models.report import AuthorReport, InstitutionReport


async def render_template_report(report: AuthorReport | InstitutionReport) -> str:
    """Render report template.

    Render the report to typst format using the templates.

    Args:
        report: Report Model.

    Returns:
        Report in Typst language.

    Raises:
        NotImplementedError: If report is `InstitutionReport` type.
    """
    if isinstance(report, AuthorReport):
        templates_path = pathlib.Path(__file__).parent.resolve().joinpath("templates/author")
    if isinstance(report, InstitutionReport):
        raise NotImplementedError

    # Render template
    env = Environment(loader=FileSystemLoader(searchpath=templates_path), enable_async=True, trim_blocks=True, lstrip_blocks=True)
    return await env.get_template("report.typ").render_async(report=report, version=version('pub-analyzer'))


async def render_report(report: AuthorReport | InstitutionReport, file_path: pathlib.Path) -> bytes:
    """Render report to PDF.

    The specified path is not where the PDF file will be saved. The path is where the typst
    file will be created (You can create a temporary path using the `tempfile` package).
    This is done in this way because at the moment the typst package can only read the
    document to be compiled from a file.

    Args:
        report: Report Model.
        file_path: Temporary directory for the typst file.

    Returns:
        PDF bytes.

    Raises:
        SyntaxError: If typst compiler syntax error.
    """
    template_render = await render_template_report(report=report)

    # Write template to typst file
    root = file_path.parent
    temp_file = open(root.joinpath(file_path.stem + ".typ"), mode="w", encoding="utf-8")
    temp_file.write(template_render)
    temp_file.close()

    # Render typst file
    pdf_render = typst.compile(temp_file.name)

    if isinstance(pdf_render, bytes):
        return pdf_render
    else:
        raise SyntaxError
