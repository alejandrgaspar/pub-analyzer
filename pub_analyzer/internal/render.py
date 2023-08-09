"""Render reports."""

import pathlib

from jinja2 import Environment, FileSystemLoader

from pub_analyzer.models.report import AuthorReport


async def render_author_report(report: AuthorReport) -> str:
    """Render author report pdf."""
    templates_path = pathlib.Path(__file__).parent.resolve().joinpath("templates/author")
    env = Environment(loader=FileSystemLoader(searchpath=templates_path), enable_async=True, trim_blocks=True, lstrip_blocks=True)

    return await env.get_template("report.typ").render_async(report=report)
