# Test Execution Guide: Allure Reporting, Parallel & Random Ordering

This guide covers how to run tests with enhanced pytest plugins, Allure reporting, parallel execution, and randomized test ordering.

## Quick Start

### Prerequisites

Ensure dependencies are installed:

```bash
poetry install
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `pytest-xdist` - Parallel test execution
- `pytest-randomly` - Randomized test ordering
- `pytest-timeout` - Test timeout handling
- `allure-pytest` - Allure reporting integration

### Installing Allure Report Viewer (Optional)

To view Allure reports locally, install the Allure Report CLI:

**macOS:**
```bash
brew install allure
```

**Linux (apt):**
```bash
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

**Windows (Chocolatey):**
```bash
choco install allure
```

---

## Running Tests

### Basic Test Run (Unit Tests)

```bash
poetry run pytest tests/unit/ -v
```

### All Tests with Coverage

```bash
poetry run pytest tests/ -v --cov=src/ --cov-report=html --cov-report=term-missing
```

### Parallel Execution

Run tests in parallel using all available CPU cores:

```bash
poetry run pytest tests/ -n auto -v
```

Or specify a specific number of workers:

```bash
poetry run pytest tests/ -n 4 -v
```

**Benefits:**
- Faster feedback on large test suites
- Especially good for unit tests (no browser interaction conflicts)

**Caution:**
- Smoke tests (those launching browsers) should be run sequentially or with limited parallelism if they share resources

### Randomized Test Ordering

Run tests in random order to surface hidden dependencies:

```bash
poetry run pytest tests/ -v --randomly-dont-shuffle-python-modules
```

**Partial randomization (within test files only):**

```bash
poetry run pytest tests/ -v --randomly-seed=12345
```

**Use a fixed seed for reproducibility:**

```bash
poetry run pytest tests/ -v --randomly-seed=12345
```

### Combining Parallelism and Random Order

```bash
poetry run pytest tests/ -n auto -v --randomly-dont-shuffle-python-modules
```

---

## Allure Reporting

### Generate Allure Report

Run tests and generate Allure artifacts:

```bash
poetry run pytest tests/ --alluredir=allure-results -v
```

### View Allure Report (Interactive)

After generating the report, start the Allure reporting server:

```bash
allure serve allure-results/
```

This opens a browser with the interactive Allure report, showing:
- Test results and timeline
- Pass/fail metrics per marker (unit vs. smoke)
- Logs and attachments (screenshots, Selenium logs)
- Trends over time (if persistent)

### Generate Static HTML Report

Generate a static HTML report (no server needed):

```bash
allure generate allure-results/ -o allure-report/ --clean
allure-report/index.html
```

---

## Recommended Test Strategies

### 1. Fast Feedback (Unit Tests Only)

```bash
poetry run pytest tests/unit/ -n auto --randomly-dont-shuffle-python-modules -v
```

**Time:** ~5-10 seconds  
**Parallelism:** Full, no conflicts

---

### 2. Full Test Suite with Coverage

```bash
poetry run pytest tests/ -v \
    --cov=src/ --cov-report=html --cov-report=term-missing \
    --alluredir=allure-results
```

**Then view:**
```bash
allure serve allure-results/
open htmlcov/index.html
```

---

### 3. Integration Tests with Logging

```bash
poetry run pytest tests/smoke/ -v --log-cli-level=DEBUG --alluredir=allure-results
```

---

### 4. Continuous Development (Watch Mode)

Use pytest's built-in support with `--lf` (last failed) and `--ff` (failed first):

```bash
poetry run pytest tests/ -v --lf
```

Run only the last failed tests

```bash
poetry run pytest tests/ -v --ff
```

Run failed tests first, then others

---

## Configuration

### pytest.ini Options

The following are pre-configured in `pytest.ini`:

```ini
timeout = 300              # Max 5 minutes per test
log_cli_level = WARNING    # Console log level
log_file_level = DEBUG     # File log level (more verbose)
xfail_strict = false       # Don't fail on xfail marks
```

### Environment Variables

**Disable random ordering (if tests are flaky):**

```bash
PYTHONHASHSEED=0 poetry run pytest tests/
```

**Disable parallelism for debugging:**

```bash
poetry run pytest tests/ -n 0 -v
```

**Set Allure results directory:**

```bash
poetry run pytest tests/ --alluredir=/custom/path/
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests with Allure

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests with Allure
        run: |
          poetry run pytest tests/ \
            -n auto \
            -v \
            --cov=src/ \
            --cov-report=xml \
            --alluredir=allure-results
      
      - name: Upload Allure Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: allure-results
          path: allure-results/
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

Then download and view locally:

```bash
allure serve downloaded-allure-results/
```

---

## Troubleshooting

### Tests Fail in Parallel but Pass Sequentially

This indicates flaky test isolation—usually caused by shared mocks, file I/O, or browser state.

**Solution:** Run with limited workers or sequentially to identify the conflicting tests:

```bash
poetry run pytest tests/ -n 1 -v --tb=short
```

Then run individually to narrow down:

```bash
poetry run pytest tests/unit/test_module.py::TestClass::test_name -v -s
```

### Allure Server Won't Start

Ensure Allure CLI is properly installed:

```bash
allure --version
```

If missing, reinstall:

```bash
brew install allure  # macOS
# or
sudo apt-get install allure  # Linux
```

### Random Seed Not Reproducible

Always use `--randomly-seed=<value>` explicitly:

```bash
poetry run pytest tests/ -v --randomly-seed=12345
```

---

## Best Practices

1. **Run unit tests in parallel** - They're isolated and fast
2. **Run smoke tests sequentially** - Browser tests require device/resource exclusivity
3. **Use Allure for CI** - Excellent for tracking issues across runs
4. **Set a fixed seed for CI** - Reproducible failures in CI/CD
5. **Keep tests isolated** - No shared state between tests
6. **Use `--lf` locally** - Quick feedback on failures

---

## Related Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-xdist (Parallelism)](https://pytest-xdist.readthedocs.io/)
- [pytest-randomly](https://github.com/pytest-dev/pytest-randomly)
- [Allure Framework Documentation](https://docs.qameta.io/allure/)
