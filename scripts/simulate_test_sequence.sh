#!/usr/bin/env bash
# Simulate sequential test runs: unit then smoke, each producing junit, coverage, and allure results.
# Then generate and serve the Allure report.

set -euo pipefail

# Clean previous results
echo "Cleaning previous results..."
rm -rf allure-results allure-report junit.xml coverage.xml htmlcov
mkdir -p allure-results

# Run unit tests
UNIT_JUNIT=junit-unit.xml
UNIT_COV=coverage-unit.xml
echo "Running unit tests..."
poetry run pytest tests/unit --junitxml=$UNIT_JUNIT --cov=src --cov-report=xml:$UNIT_COV --alluredir=allure-results/unit || echo "Unit tests failed, continuing..."

# Run smoke tests
SMOKE_JUNIT=junit-smoke.xml
SMOKE_COV=coverage-smoke.xml
echo "Running smoke tests..."
poetry run pytest tests/smoke --junitxml=$SMOKE_JUNIT --cov=src --cov-report=xml:$SMOKE_COV --alluredir=allure-results/smoke || echo "Smoke tests failed, continuing..."


# Optionally merge junit and coverage (not required for Allure, but for completeness)
# You can use junitparser and coverage combine if needed

# Generate Allure report
echo "Generating Allure report..."
poetry run allure generate allure-results/smoke allure-results/unit --clean -o allure-report

# Serve Allure report
echo "Serving Allure report at http://localhost:8000 ..."
poetry run allure open allure-report
