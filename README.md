
# browser_launcher
Python tool that launches a browser using selenium and manages authentication.

## Linting and Static Analysis

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and [mypy](https://mypy.readthedocs.io/) for static type checking.

To run ruff (linting):

```bash
poetry run ruff check src/ tests/
```

To run ruff (format):
```bash
poetry run ruff format
```

To run mypy (type checking):

```bash
poetry run mypy src/ tests/
```

Configuration for both tools is in [pyproject.toml](pyproject.toml).

## Poetry

This project uses Poetry for dependency management and packaging.

- Install Poetry (recommended):

```bash
curl -sSL https://install.python-poetry.org | python3 -
# or follow https://python-poetry.org/docs/
```

- Create and activate the virtual environment with Poetry and install dependencies:

```bash
poetry install
```

- Run the CLI provided by this package:

```bash
poetry run browser-launcher
# or
poetry run python -m browser_launcher
```

- Add a dependency:

```bash
poetry add <package>
```

- Add a dev dependency:

```bash
poetry add --dev pytest
```

If you want me to run `poetry init` or install dependencies in this environment, tell me and I will provide the commands.
