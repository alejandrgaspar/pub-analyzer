"""Render reports."""

import logging
import pathlib
import time
from importlib.metadata import version

import typst

from pub_analyzer.models.report import AuthorReport, InstitutionReport

logger = logging.getLogger(__name__)


def render_report(report: AuthorReport | InstitutionReport, file_path: pathlib.Path | None) -> bytes | None:
    """Render report to PDF.

    Args:
        report: Report Model.
        file_path: Path to save the compiled file.

    Returns:
        PDF bytes or None if output file path is defined.

    Raises:
        SyntaxError: If typst compiler syntax error.
    """
    if isinstance(report, AuthorReport):
        templates_path = pathlib.Path(__file__).parent.resolve().joinpath("templates")
        typst_file = templates_path / "author_report.typ"
    if isinstance(report, InstitutionReport):
        raise NotImplementedError

    sys_inputs = {"report": report.model_dump_json(by_alias=True), "version": version("pub-analyzer")}

    start_time = time.time()
    if file_path:
        result = typst.compile(input=typst_file, output=file_path, sys_inputs=sys_inputs)
    else:
        result = typst.compile(input=typst_file, sys_inputs=sys_inputs)

    logger.info(f"Typst compile time: {round((time.time() - start_time), 2)} seconds.")
    return result
