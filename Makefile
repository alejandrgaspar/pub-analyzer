typecheck:
	poetry run mypy pub_analyzer

format:
	poetry run ruff pub_analyzer

dev:
	poerty run textual run --dev pub_analyzer/main.py
