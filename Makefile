typecheck:
	poetry run mypy pub_analyzer tests

format:
	poetry run ruff check pub_analyzer tests

dev:
	poetry run textual run --dev pub_analyzer.main:PubAnalyzerApp

console:
	poetry run textual console

test:
	poetry run pytest -vv --block-network

test-record:
	poetry run pytest --record-mode=once

docs-serve:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build
