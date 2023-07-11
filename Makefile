typecheck:
	poetry run mypy pub_analyzer tests

format:
	poetry run ruff check pub_analyzer tests

dev:
	poetry run textual run --dev pub_analyzer/main.py

console:
	poetry run textual console

test:
	poetry run pytest -vv
