run := poetry run

typecheck:
	$(run) mypy pub_analyzer tests

lint:
	$(run) ruff check pub_analyzer tests

format:
	$(run) ruff format pub_analyzer tests

dev:
	$(run) textual run --dev pub_analyzer.main:PubAnalyzerApp

console:
	$(run) textual console

debug-console:
	$(run) textual console -x EVENT -x DEBUG -x SYSTEM -x WORKER

test:
	$(run) pytest -vv --block-network

test-record:
	$(run) pytest --record-mode=once

docs-serve:
	$(run) mkdocs serve --livereload

docs-clean-screenshot-cache:
	rm -rf .screenshot_cache

docs-build: docs-clean-screenshot-cache
	$(run) mkdocs build
