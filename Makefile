typecheck:
	poetry run mypy pub_analyzer

format:
	poetry run ruff pub_analyzer

dev:
	poetry run textual run --dev pub_analyzer/main.py

console:
	poetry run textual console
