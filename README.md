# browser_launcher

A powerful Python CLI tool for launching and managing browsers (Chrome, Firefox, Safari, Edge) using Selenium, with advanced features for authentication, cookie management, and automated workflows.

## ✨ Features

- 🌐 **Multi-Browser Support**: Chrome, Firefox, Safari, and Edge
- 🍪 **Smart Cookie Management**: Hierarchical cookie profiles by user, environment, and domain
- 📸 **Interactive Screenshots**: Capture screenshots with a single keypress
- 🔐 **Authentication Handling**: Automated cookie injection for seamless authentication
- ⚙️ **Flexible Configuration**: TOML-based configuration with extensive customization
- 🎮 **Interactive Session**: Real-time keyboard controls for screenshots and cookie saving
- 📝 **Comprehensive Logging**: Structured logging with configurable verbosity levels
- 🧪 **Well-Tested**: 300+ tests ensuring reliability and stability

## 📋 Requirements

- Python 3.14 or higher
- Poetry (for dependency management)
- Browser drivers (automatically managed by Selenium 4.40.0+)

## 🚀 Installation

### Using Poetry (Recommended)

1. **Install Poetry** if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # or follow https://python-poetry.org/docs/
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/RamonAlcantaraArceo/browser_launcher.git
   cd browser_launcher
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## ⚡ Quick Start

### Initialize Configuration

First, initialize the browser launcher configuration:

```bash
poetry run browser-launcher init
```

This creates:
- `~/.browser_launcher/` directory
- `~/.browser_launcher/config.toml` configuration file
- `~/.browser_launcher/logs/` directory for logs

### Launch a Browser

Launch Chrome with a specific URL:

```bash
poetry run browser-launcher launch https://github.com
```

Launch Firefox instead:

```bash
poetry run browser-launcher launch https://github.com --browser firefox
```

Launch in headless mode:

```bash
poetry run browser-launcher launch https://github.com --headless
```

### Interactive Session Controls

Once the browser is launched, you can:

- **Press Enter**: Capture a screenshot
- **Press 's'**: Save/cache current browser cookies to config
- **Press Ctrl+D**: Exit and close the browser

## 📖 Usage

### Commands

#### `init` - Initialize Configuration

Initialize the browser launcher configuration directory and files.

```bash
browser-launcher init [OPTIONS]
```

**Options:**
- `--force`: Force reinitialize even if directory exists
- `--verbose, -v`: Show detailed operational logs (INFO level)
- `--debug`: Enable comprehensive debugging logs (DEBUG level)

**Example:**
```bash
browser-launcher init --verbose
browser-launcher init --force  # Reinitialize existing config
```

#### `launch` - Launch Browser

Launch a browser with specified options.

```bash
browser-launcher launch [URL] [OPTIONS]
```

**Arguments:**
- `URL`: URL to open (optional, uses default from config if not specified)

**Options:**
- `--browser TEXT`: Browser to use (chrome, firefox, safari, edge)
- `--headless`: Run browser in headless mode
- `--user TEXT`: User profile for cookie lookup (default: 'default')
- `--env TEXT`: Environment for cookie lookup (default: 'prod')
- `--verbose, -v`: Show detailed operational logs
- `--debug`: Enable debugging logs

**Examples:**
```bash
# Launch with default settings
browser-launcher launch https://example.com

# Launch specific browser
browser-launcher launch https://example.com --browser firefox

# Launch with headless mode
browser-launcher launch https://example.com --headless

# Launch with specific user and environment for cookies
browser-launcher launch https://example.com --user alice --env staging

# Launch with verbose logging
browser-launcher launch https://example.com --verbose
```

#### `clean` - Clean Configuration

Remove browser launcher configuration directory and files.

```bash
browser-launcher clean [OPTIONS]
```

**Options:**
- `--force`: Force cleanup without confirmation
- `--yes, -y`: Skip confirmation prompt
- `--verbose, -v`: Show detailed operational logs
- `--debug`: Enable debugging logs

**Example:**
```bash
browser-launcher clean --yes
```

## ⚙️ Configuration

The configuration file is located at `~/.browser_launcher/config.toml`.

### Basic Configuration

```toml
[settings]
default_browser = "chrome"
default_url = "http://example.com"
console_logging = false
logging_level = "WARNING"

[browsers.chrome]
binary_path = "/usr/bin/google-chrome"
headless = false
user_data_dir = ""
custom_flags = ["--disable-gpu", "--no-sandbox"]

[browsers.firefox]
binary_path = "/usr/bin/firefox"
headless = false

[browsers.safari]
# Safari uses system default

[browsers.edge]
binary_path = "/usr/bin/microsoft-edge"
```

### Cookie Configuration

Cookies are organized hierarchically by user, environment, and domain:

```toml
[users.default.prod.cookies]
session_token = { domain = ".example.com", path = "/", secure = true }
auth_cookie = { domain = ".example.com", path = "/api", secure = true }

[users.alice.staging.cookies]
session_token = { domain = ".staging.example.com", path = "/", secure = true }
```

**Cookie Cache:**
Cached cookie values are stored under each cookie definition:

```toml
[users.default.prod.cookies.session_token]
domain = ".example.com"
path = "/"
secure = true

[users.default.prod.cookies.session_token.cache]
value = "encrypted_session_value_here"
timestamp = "2026-02-26T10:30:00"
```

## 🍪 Cookie Management

### Saving Cookies

1. Launch browser with your user/env profile:
   ```bash
   browser-launcher launch https://example.com --user myuser --env prod
   ```

2. Log in to the website manually

3. Press **'s'** to save cookies to the config file

4. Cookies are now cached and will auto-inject on next launch

### Cookie Injection

Cookies are automatically injected when:
- A valid cookie cache exists for the user/env/domain combination
- The browser navigates to a matching domain
- Cookie values are still valid

## 📸 Screenshots

Screenshots are captured interactively during browser sessions:

1. While the browser is running, press **Enter**
2. Screenshot is saved to `~/Downloads/` with timestamp-based filename
3. Filename format: `screenshot_YYYYMMDD_HHMMSS_microseconds.png`

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/RamonAlcantaraArceo/browser_launcher.git
cd browser_launcher

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

This project uses [pytest](https://pytest.org/) with advanced plugins for parallel execution, test randomization, and Allure reporting.

**Quick test runs:**
```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=src/ --cov-report=html

# Run specific test file
poetry run pytest tests/test_cli_launch.py -v

# Run specific test
poetry run pytest tests/test_cli_launch.py::test_launch_success -v
```

**Advanced testing (parallel, random order, Allure reports):**

See [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for comprehensive testing instructions including:
- Parallel execution with `pytest-xdist` (`-n auto`)
- Randomized test ordering with `pytest-randomly`
- Interactive Allure HTML reports with `allure-pytest`
- Code coverage tracking with `pytest-cov`

**Installing Allure Report Viewer (Optional):**

To view interactive Allure test reports locally:

macOS:
```bash
brew install allure
```

Linux (apt):
```bash
sudo apt-add-repository ppa:qameta/allure && sudo apt-get update && sudo apt-get install allure
```

Windows (Chocolatey):
```bash
choco install allure
```

Then generate and view reports:
```bash
poetry run pytest tests/unit/ -v --alluredir=allure-results
allure serve allure-results/
```

### Allure in CI matrix runs

The Allure GitHub Actions workflow runs the unit suite across Python 3.13–3.14 and merges all `allure-results` artifacts into one report.

- Each test case is tagged with a `python_version` Allure parameter (for example, `Python 3.11`).
- The same value is also applied as an Allure sub-suite label so the report can be navigated by Python version.
- Categories are used for failure classification and are not used to split results by Python version.

If the merged report looks like a single run instead of matrix totals, verify:

- Test execution includes `ALLURE_PYTHON_VERSION` for each matrix job.
- Pytest runs with `--alluredir=allure-results`.
- The publish job merges all `allure-results-*` artifacts before generating the report.

Local matrix simulation example:
```bash
ALLURE_PYTHON_VERSION=3.11 poetry run pytest tests/unit/ -v --alluredir=allure-results
```
poetry run pytest tests/ --alluredir=allure-results
allure serve allure-results/
```

### Code Quality

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting, and [mypy](https://mypy.readthedocs.io/) for static type checking.

**Format code:**
```bash
poetry run ruff format
```

**Lint code:**
```bash
poetry run ruff check src/ tests/
```

**Fix linting issues automatically:**
```bash
poetry run ruff check src/ tests/ --fix
```

**Type checking:**
```bash
poetry run mypy src/ tests/
```

**Run all checks:**
```bash
poetry run ruff format && poetry run ruff check src/ tests/ && poetry run mypy src/ tests/
```

### Adding Dependencies

**Production dependency:**
```bash
poetry add <package>
```

**Development dependency:**
```bash
poetry add --group dev <package>
```

## 🏗️ Architecture

The project follows a modular architecture:

```
src/browser_launcher/
├── cli.py              # CLI interface (Typer-based)
├── config.py           # Configuration management
├── cookies.py          # Cookie handling and injection
├── screenshot.py       # Screenshot utilities
├── utils.py            # Utility functions
└── browsers/
    ├── base.py         # Abstract base class
    ├── factory.py      # Browser factory pattern
    ├── chrome.py       # Chrome implementation
    ├── firefox.py      # Firefox implementation
    ├── safari.py       # Safari implementation
    └── edge.py         # Edge implementation
```

### Design Patterns

- **Factory Pattern**: Browser instantiation via `BrowserFactory`
- **Abstract Base Class**: `BrowserLauncher` defines browser interface
- **Dependency Injection**: Loggers and configs passed to components
- **Configuration as Code**: TOML-based declarative configuration

## 📚 Documentation

- [Implementation Plan](plans/IMPLEMENTATION_PLAN.md) - Detailed architecture and TDD phases
- [CHANGELOG](CHANGELOG.md) - Project changelog
- [Poetry Guide](Poetry.md) - Poetry-specific documentation

## 🧪 Testing

The project uses a comprehensive test suite with 130+ tests covering:

- CLI command functionality
- Browser factory and implementations
- Cookie management and injection
- Configuration loading and validation
- Screenshot capture
- Error handling and edge cases

**Test Organization:**
```
tests/
├── test_cli_*.py       # CLI command tests
├── test_config.py      # Configuration tests
├── test_cookies.py     # Cookie handling tests
├── test_screenshot.py  # Screenshot tests
└── browsers/           # Browser implementation tests
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`poetry run pytest`)
5. Ensure code quality checks pass (`poetry run ruff format && poetry run ruff check`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow Google-style docstrings
- Write tests before implementation (TDD approach)
- Maintain test coverage above 90%
- Use type hints throughout
- Keep functions focused and small
- Document complex logic

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Selenium](https://www.selenium.dev/) for browser automation
- CLI powered by [Typer](https://typer.tiangolo.com/)
- Rich terminal output via [Rich](https://rich.readthedocs.io/)
- Logging by [r3a-minikit](https://github.com/RamonAlcantaraArceo/r3a-minikit)

## 📞 Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/RamonAlcantaraArceo/browser_launcher).

---

**Made with ❤️ by Ramon Alcantara Arceo**
