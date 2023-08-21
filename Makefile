run := poetry run

typecheck:
	$(run) mypy pub_analyzer tests

format:
	$(run) ruff check pub_analyzer tests

dev:
	$(run) textual run --dev pub_analyzer.main:PubAnalyzerApp

console:
	$(run) textual console

test:
	$(run) pytest -vv --block-network

test-record:
	$(run) pytest --record-mode=once

docs-serve:
	$(run) mkdocs serve

docs-build:
	$(run) mkdocs build
