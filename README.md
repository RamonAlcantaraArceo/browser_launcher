# browser_launcher
Python tool that launches a browser using selenium and manages authentication.

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
