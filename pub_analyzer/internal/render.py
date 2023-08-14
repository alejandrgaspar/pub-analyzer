"""Render reports."""

import pathlib

import typst
from jinja2 import Environment, FileSystemLoader

from pub_analyzer.models.report import AuthorReport, InstitutionReport


async def render_template_report(report: AuthorReport | InstitutionReport) -> str:
    """Render report pdf."""
    if isinstance(report, AuthorReport):
        templates_path = pathlib.Path(__file__).parent.resolve().joinpath("templates/author")
    if isinstance(report, InstitutionReport):
        raise NotImplementedError

    # Render template
    env = Environment(loader=FileSystemLoader(searchpath=templates_path), enable_async=True, trim_blocks=True, lstrip_blocks=True)
    return await env.get_template("report.typ").render_async(report=report)


async def render_report(report: AuthorReport | InstitutionReport, file_path: pathlib.Path) -> bytes:
    """Render report pdf."""
    template_render = await render_template_report(report=report)

    # Write template to typst file
    root = file_path.parent
    temp_file = open(root.joinpath(file_path.stem + ".typ"), mode="w")
    temp_file.write(template_render)
    temp_file.close()

    # Render typst file
    compiler = typst.Compiler(root)
    pdf_render = compiler.compile(temp_file.name)

    if isinstance(pdf_render, bytes):
        return pdf_render
    else:
        raise SyntaxError
