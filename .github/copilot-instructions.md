# GitHub Copilot Instructions for browser_launcher

## Project Overview
- **browser_launcher** is a Python tool for launching browsers (Chrome, Firefox, Safari, Edge) using Selenium, with a focus on authentication and automation.
- The CLI is built with Typer and supports commands for launching, initializing, and cleaning up browser sessions.
- Configuration is managed via TOML files in `~/.browser_launcher/config.toml` and can be customized per browser, user, environment, and domain.
- Logging uses Python's logging module with both file and console output, and supports verbosity/debug flags.
- The project uses TDD: tests are written before implementation, and all new features require corresponding tests.

## Architecture & Patterns
- **src/browser_launcher/browsers/** contains all browser implementations. Each browser inherits from `BrowserLauncher` (abstract base class in `base.py`).
- The **factory pattern** (`factory.py`) is used to instantiate browser classes dynamically based on config/CLI input.
- **Configuration** is loaded and managed by `config.py` (see `BrowserLauncherConfig`).
- **CLI** (`cli.py`) is the main entry point for user interaction and orchestrates browser launch, config loading, and logging.
- **Cookie management** is being added as a dedicated module (`cookies.py`) with hierarchical, user/env/domain-aware config and cache.
- **Tests** are organized by component and browser, with shared fixtures in `conftest.py` and TDD phases documented in `plans/IMPLEMENTATION_PLAN.md`.

## Developer Workflows
- **Install dependencies:** `poetry install`
- **Run CLI:** `poetry run browser-launcher [command]`
- **Run tests:** `poetry run pytest tests/ -v`
- **Lint/format:** `poetry run ruff format` and `poetry run ruff check src/ tests/`
- **Type check:** `poetry run mypy src/ tests/`
- **Add dependencies:** `poetry add <package>`
- **Update config:** Edit `~/.browser_launcher/config.toml` or use `init` command

## Project Conventions
- **Docstrings:** Use Google-style docstrings for all Python code (see `.github/instructions/docstrings.md` if present)
- **TDD:** Write or update tests before implementing new features or refactoring
- **Error handling:** All CLI errors should print user-friendly messages and log details
- **Extensibility:** New browsers or features should follow the factory and base class patterns
- **Config structure:** Use hierarchical keys: `[users.{user}.{env}.{domain}]` for cookies and per-browser settings
- **Logging:** Use the provided logger, respect verbosity/debug flags, and avoid print statements in production code

## Key Files & Directories
- `src/browser_launcher/browsers/base.py`: Abstract base class for browsers
- `src/browser_launcher/browsers/factory.py`: Factory for browser instantiation
- `src/browser_launcher/config.py`: Configuration management
- `src/browser_launcher/cli.py`: CLI entry point
- `src/browser_launcher/cookies.py`: Cookie management (in progress)
- `tests/`: All tests, organized by component
- `plans/IMPLEMENTATION_PLAN.md`: Detailed architecture, TDD phases, and design decisions
- `README.md`: Quickstart, Poetry, and linting instructions

## Examples
- Launch Chrome with custom config: `poetry run browser-launcher launch https://example.com --browser chrome --user alice --env staging`
- Launch Chrome with default config: `poetry run browser-launcher launch https://example.com`
- Run tests: `poetry run pytest tests/ -v`
- Generate code coverage report: `poetry run pytest tests/ --cov=src/ --cov-report=html`
- Run all checks: `poetry run ruff format && poetry run ruff check src/ tests/ && poetry run mypy src/ tests/ && poetry run pytest tests/ -v`

---

For more details, see `plans/IMPLEMENTATION_PLAN.md` and `README.md`. If you are unsure about a pattern, check for existing tests or consult the implementation plan.
