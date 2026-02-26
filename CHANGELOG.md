# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Core Commands
- `init` command to initialize browser launcher configuration directory and files
  - Creates `~/.browser_launcher/` directory structure
  - Generates default `config.toml` configuration file
  - Creates logs directory for application logging
  - `--force` flag to reinitialize existing configuration
  - `--verbose` and `--debug` flags for detailed logging

- `launch` command to launch browsers with advanced options
  - Support for multiple browsers: Chrome, Firefox, Safari, Edge
  - URL argument to specify target website
  - `--browser` option to select specific browser
  - `--headless` mode for headless browser execution
  - `--user` option for user-specific cookie profiles (default: 'default')
  - `--env` option for environment-specific configuration (default: 'prod')
  - `--verbose` and `--debug` flags for operational logging

- `clean` command to remove browser launcher configuration
  - Interactive confirmation prompt before deletion
  - `--force` flag to skip confirmation
  - `--yes` flag as alternative confirmation skip
  - `--verbose` and `--debug` flags for detailed logging

#### Cookie Management
- Hierarchical cookie configuration by user, environment, and domain
- Automatic cookie injection on browser launch from cached values
- Interactive cookie saving during browser session (press 's')
- Cookie verification after injection
- Support for multiple domains per user/environment profile
- Cookie cache updates written to config file

#### Screenshot Capabilities
- Interactive screenshot capture during browser session (press Enter)
- Automatic screenshot naming with timestamp-based ID generation
- Screenshots saved to Downloads directory by default
- Configurable delay before capture

#### Interactive Session Control
- Unbuffered keyboard input for immediate command response
- Press Enter: Capture screenshot
- Press 's': Save/cache current browser cookies
- Press Ctrl+D: Exit and close browser
- Session health monitoring with auto-detection of disconnected sessions

#### Logging System
- Integration with r3a_logger for structured logging
- File-based logging to `~/.browser_launcher/logs/`
- Console logging controlled by configuration and CLI flags
- Log levels: DEBUG, INFO, WARNING, ERROR
- Configurable log rotation and cleanup
- Separate logging for user-facing output vs debug information

#### Configuration Management
- TOML-based configuration file format
- Default browser and URL settings
- Per-browser configuration with custom flags
- Binary path configuration for browsers
- User data directory customization
- Headless mode defaults
- Console logging preferences
- Logging level configuration
- Extra options and custom flags support

#### Browser Support
- Chrome browser with ChromeDriver integration
- Firefox browser with GeckoDriver integration
- Safari browser with native driver support (macOS)
- Edge browser with EdgeDriver integration
- Factory pattern for browser instantiation
- Extensible architecture for adding new browsers

#### Development Tools
- Comprehensive test suite with 130+ tests
- pytest-based testing framework
- Test coverage reporting
- Type checking with mypy
- Code formatting with ruff
- Linting with ruff
- Poetry-based dependency management
- Pre-configured VS Code tasks

### Technical Details
- Python 3.10+ support
- Selenium WebDriver integration
- Rich library for enhanced console output
- Typer for CLI framework
- Google-style docstrings throughout codebase
- TDD (Test-Driven Development) approach
- Abstract base class pattern for browser implementations

[Unreleased]: https://github.com/RamonAlcantaraArceo/browser_launcher/compare/main...HEAD
