run := uv run

typecheck:
	$(run) ty check pub_analyzer tests

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

coverage:
	$(run) pytest --block-network --cov --cov-report=term-missing

# Coverage excluding the cassette-backed integration test, to track how much
# of the codebase is reachable without recorded network traffic.
coverage-offline:
	$(run) pytest --block-network --cov --cov-report=term-missing \
		--ignore=tests/internal/test_make_report.py

docs-serve:
	$(run) mkdocs serve --livereload

docs-clean-screenshot-cache:
	rm -rf .screenshot_cache

docs-build: docs-clean-screenshot-cache
	$(run) mkdocs build
