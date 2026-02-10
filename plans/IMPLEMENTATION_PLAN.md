# Browser Launcher - Complete Implementation Plan

## Table of Contents

1. [Overview & Problem Statement](#overview--problem-statement)
2. [Proposed Architecture](#proposed-architecture)
3. [Design Patterns & Components](#design-patterns--components)
4. [TDD Implementation Phases](#tdd-implementation-phases)
5. [Testing Strategy](#testing-strategy)
6. [Success Criteria](#success-criteria)

---

## Overview & Problem Statement

### Context

The browser launcher project needs to support multiple browsers with a clean, extensible architecture.

### Challenges

- **Chrome** has extensive flag support (50+) with many optimization and behavior options
- **Safari** is opinionated and doesn't allow easy programmatic interaction
- **Firefox** and **Edge** have moderate flag support
- Current code has a placeholder `launch()` function with no actual browser implementation
- Need clean architecture that prevents complexity from growing across all browsers

### Solution Approach

Use **Test-Driven Development (TDD)** with modular architecture:
- Separate `browsers/` directory with individual modules for each browser
- Abstract Base Class defining consistent interface
- Factory pattern for browser instantiation
- Configuration management for browser-specific settings

---

## Proposed Architecture

### Directory Structure

```
src/browser_launcher/
├── browsers/                    # NEW: Browser implementations
│   ├── __init__.py
│   ├── base.py                 # Abstract base class defining browser interface
│   ├── chrome.py               # Chrome-specific implementation
│   ├── firefox.py              # Firefox-specific implementation
│   ├── safari.py               # Safari-specific implementation
│   ├── edge.py                 # Edge-specific implementation
│   └── factory.py              # Factory pattern for browser selection
├── config.py                   # NEW: Configuration management
├── cli.py                      # UPDATED: CLI commands
├── logger.py                   # EXISTING: Logging infrastructure
└── __main__.py                 # EXISTING: Entry point
```

### Design Patterns Used

#### 1. **Abstract Base Class (ABC)**
- `browsers/base.py` defines the contract all browsers must follow
- Ensures consistent interface across all implementations
- Enforces required methods: `launch()`, `validate_binary()`, `build_command_args()`

#### 2. **Factory Pattern**
- `browsers/factory.py` handles browser instantiation
- Centralizes browser selection logic
- Returns appropriate browser instance based on user input

#### 3. **Configuration Management**
- `config.py` loads and parses TOML configuration
- Provides browser-specific settings from config file
- Handles binary path resolution and validation

#### 4. **Strategy Pattern (Implicit)**
- Each browser module encapsulates its own flag-building strategy
- Chrome can use aggressive optimization flags
- Safari can use minimal/no flags as appropriate

---

## Design Patterns & Components

### 1. `browsers/base.py` - Abstract Base Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import subprocess

@dataclass
class BrowserConfig:
    """Configuration for a browser instance."""
    binary_path: Optional[Path]
    headless: bool
    user_data_dir: Optional[Path]
    custom_flags: Optional[List[str]]

class BrowserLauncher(ABC):
    """Abstract base class for all browser implementations."""
    
    def __init__(self, config: BrowserConfig, logger):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def validate_binary(self) -> bool:
        """Check if browser binary exists and is executable."""
        pass
    
    @abstractmethod
    def build_command_args(self, url: str) -> List[str]:
        """Build command-line arguments for launching the browser."""
        pass
    
    @abstractmethod
    def launch(self, url: str) -> subprocess.Popen:
        """Launch the browser with the given URL."""
        pass
    
    @property
    @abstractmethod
    def browser_name(self) -> str:
        """Return the browser name (chrome, firefox, etc)."""
        pass
```

### 2. `browsers/chrome.py` - Chrome Implementation

**Handles:**
- Chrome-specific flags (--disable-sync, --disable-default-apps, etc.)
- User data directory management
- Headless mode
- Custom flags from config
- Binary path detection (standard locations)

**Key features:**
- Extensive flag support for development/testing
- Handles user profiles
- Disables sync and notifications for cleaner testing

### 3. `browsers/firefox.py` - Firefox Implementation

**Handles:**
- Firefox-specific preferences (prefs.js)
- Profile management
- Headless mode via -headless flag
- Custom flags

### 4. `browsers/safari.py` - Safari Implementation

**Handles:**
- Limited flag support (Safari doesn't expose most options)
- Respects Safari's opinionated design
- Focus on basic URL launching
- May use AppleScript for advanced interactions

### 5. `browsers/edge.py` - Edge Implementation

**Handles:**
- Edge-specific flags (similar to Chrome)
- User data directory
- Headless mode
- Binary path detection

### 6. `browsers/factory.py` - Factory Pattern

```python
class BrowserFactory:
    """Factory for creating browser instances."""
    
    _browsers = {
        'chrome': ChromeLauncher,
        'firefox': FirefoxLauncher,
        'safari': SafariLauncher,
        'edge': EdgeLauncher,
    }
    
    @classmethod
    def create(cls, browser_name: str, config: BrowserConfig, logger) -> BrowserLauncher:
        """Create and return a browser instance."""
        if browser_name not in cls._browsers:
            raise ValueError(f"Unsupported browser: {browser_name}")
        
        browser_class = cls._browsers[browser_name]
        return browser_class(config, logger)
    
    @classmethod
    def get_available_browsers(cls) -> List[str]:
        """Return list of supported browsers."""
        return list(cls._browsers.keys())
```

### 7. `config.py` - Configuration Management

**Handles:**
- Loading TOML config from `~/.browser_launcher/config.toml`
- Parsing browser-specific settings
- Resolving binary paths
- Providing defaults
- Caching loaded configuration

```python
class BrowserLauncherConfig:
    """Load and manage browser launcher configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path.home() / ".browser_launcher" / "config.toml")
        self.config_data = self._load_config()
    
    def get_browser_config(self, browser_name: str, headless: bool = False) -> BrowserConfig:
        """Get configuration for a specific browser."""
        # Returns BrowserConfig with merged defaults + user settings
        pass
    
    def get_default_browser(self) -> str:
        """Get the default browser from config."""
        pass
    
    def get_default_url(self) -> str:
        """Get the default URL from config."""
        pass
```

### 8. Updated `cli.py` - Launch Command

```python
@app.command()
def launch(
    url: Optional[str] = typer.Argument(None, help="URL to open"),
    browser: Optional[str] = typer.Option(None, "--browser", help="Browser to use"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed operational logs"),
    debug: bool = typer.Option(False, "--debug", help="Enable comprehensive debugging logs")
):
    """Launch a browser with specified options."""
    initialize_logging(verbose=verbose, debug=debug)
    logger = get_current_logger()
    
    # Load configuration
    config = BrowserLauncherConfig()
    browser_name = browser or config.get_default_browser()
    
    # Create browser instance
    browser_config = config.get_browser_config(browser_name, headless=headless)
    browser_launcher = BrowserFactory.create(browser_name, browser_config, logger)
    
    # Validate and launch
    if not browser_launcher.validate_binary():
        logger.error(f"Browser binary not found: {browser_name}")
        console.print(f"❌ Browser not found: {browser_name}")
        sys.exit(1)
    
    try:
        process = browser_launcher.launch(url or config.get_default_url())
        console.print(f"✅ Launched {browser_name} with URL: {url}")
        logger.info(f"Successfully launched {browser_name}")
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}", exc_info=True)
        console.print(f"❌ Error: {e}")
        sys.exit(1)
```

### Key Design Decisions

#### Why Separate Modules?
- Each browser has unique binary paths, flags, and behaviors
- Changes to Chrome flags don't affect Safari
- Easy to add/remove browser support
- Cleaner testing with mocked browser implementations

#### Why Abstract Base Class?
- Ensures consistent interface across all browsers
- Type checking and IDE autocomplete
- Forces implementation of required methods
- Clear contract for future browsers

#### Why Factory Pattern?
- Centralizes browser selection logic
- Easy to support dynamic browser discovery
- Extensible without modifying CLI code
- Simplifies testing with mock factories

#### Why TOML Configuration?
- Human-readable format
- Already defined in config template
- Easy to extend per-browser settings
- Supports profiles and presets

### Browser-Specific Considerations

#### Chrome
- Most flexible with extensive flag support
- Supports user profiles, cache management
- Can be heavily customized
- Binary paths: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (macOS)

#### Firefox
- Profile management important
- Limited but sufficient flag support
- Headless mode via `-headless`
- Binary paths: `/Applications/Firefox.app/Contents/MacOS/firefox` (macOS)

#### Safari
- Very limited programmatic control
- No traditional flags like Chrome/Firefox
- Respects Safari's opinionated design
- Should focus on basic URL launching
- Binary: `/Applications/Safari.app` (macOS)

#### Edge
- Similar to Chrome (Chromium-based)
- Supports many Chrome flags with minor changes
- User data directory management
- Binary paths: `/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge` (macOS)

---

## TDD Implementation Phases

### TDD Workflow

For each component, follow the Red-Green-Refactor cycle:

1. **RED**: Write a failing test that describes desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Clean up code while tests still pass

---

### Phase 1: Base Class & Abstraction (Foundation)

#### Step 1.1: Write Base Class Tests

**File**: `tests/browsers/test_base.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.base import BrowserLauncher, BrowserConfig

class TestBrowserLauncherInterface:
    """Define the contract all browser implementations must follow."""
    
    def test_browser_launcher_is_abstract(self):
        """Base class cannot be instantiated directly."""
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        with pytest.raises(TypeError):
            BrowserLauncher(config, mock.Mock())
    
    def test_browser_launcher_requires_launch_implementation(self):
        """All browsers must implement launch()."""
        class IncompleteChrome(BrowserLauncher):
            def validate_binary(self): return True
            def build_command_args(self, url): return []
            @property
            def browser_name(self): return "chrome"
        
        with pytest.raises(TypeError):
            IncompleteChrome(BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None), mock.Mock())
    
    def test_browser_launcher_requires_validate_binary(self):
        """All browsers must implement validate_binary()."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url): return mock.Mock()
            def build_command_args(self, url): return []
            @property
            def browser_name(self): return "chrome"
        
        with pytest.raises(TypeError):
            IncompleteChrome(BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None), mock.Mock())
    
    def test_browser_launcher_requires_build_command_args(self):
        """All browsers must implement build_command_args()."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url): return mock.Mock()
            def validate_binary(self): return True
            @property
            def browser_name(self): return "chrome"
        
        with pytest.raises(TypeError):
            IncompleteChrome(BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None), mock.Mock())
    
    def test_browser_launcher_requires_browser_name_property(self):
        """All browsers must implement browser_name property."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url): return mock.Mock()
            def validate_binary(self): return True
            def build_command_args(self, url): return []
        
        with pytest.raises(TypeError):
            IncompleteChrome(BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None), mock.Mock())

class TestBrowserConfig:
    """Test BrowserConfig data structure."""
    
    def test_browser_config_stores_binary_path(self):
        config = BrowserConfig(binary_path="/usr/bin/chrome", headless=False, user_data_dir=None, custom_flags=None)
        assert config.binary_path == "/usr/bin/chrome"
    
    def test_browser_config_stores_headless_mode(self):
        config = BrowserConfig(binary_path="/usr/bin/chrome", headless=True, user_data_dir=None, custom_flags=None)
        assert config.headless is True
    
    def test_browser_config_stores_user_data_dir(self):
        config = BrowserConfig(binary_path="/usr/bin/chrome", headless=False, user_data_dir="/tmp/profile", custom_flags=None)
        assert config.user_data_dir == "/tmp/profile"
    
    def test_browser_config_stores_custom_flags(self):
        flags = ["--disable-sync", "--no-first-run"]
        config = BrowserConfig(binary_path="/usr/bin/chrome", headless=False, user_data_dir=None, custom_flags=flags)
        assert config.custom_flags == flags
```

**Then implement**: `src/browser_launcher/browsers/base.py`

---

### Phase 2: Chrome Browser Implementation

#### Step 2.1: Write Chrome Tests

**File**: `tests/browsers/test_chrome.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.base import BrowserConfig

class TestChromeBuildCommandArgs:
    """Test Chrome argument building logic."""
    
    def test_chrome_command_includes_binary_path(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[0] == "/usr/bin/google-chrome"
    
    def test_chrome_command_includes_url_as_last_arg(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[-1] == "https://example.com"
    
    def test_chrome_headless_adds_flag(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=True, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--headless" in args
    
    def test_chrome_no_headless_excludes_flag(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--headless" not in args
    
    def test_chrome_adds_user_data_dir(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir="/tmp/profile", custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--user-data-dir=/tmp/profile" in args
    
    def test_chrome_adds_custom_flags(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=["--disable-sync", "--no-first-run"])
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--disable-sync" in args
        assert "--no-first-run" in args

class TestChromeBinaryValidation:
    """Test Chrome binary path validation."""
    
    @mock.patch('pathlib.Path.exists')
    @mock.patch('os.access', return_value=True)
    def test_chrome_validates_existing_binary(self, mock_access, mock_exists):
        mock_exists.return_value = True
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.validate_binary() is True
    
    @mock.patch('pathlib.Path.exists', return_value=False)
    def test_chrome_rejects_nonexistent_binary(self, mock_exists):
        config = BrowserConfig(binary_path="/nonexistent/chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.validate_binary() is False

class TestChromeLaunch:
    """Test Chrome launch execution."""
    
    @mock.patch('subprocess.Popen')
    def test_chrome_launch_calls_subprocess(self, mock_popen):
        mock_process = mock.Mock()
        mock_popen.return_value = mock_process
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        result = browser.launch("https://example.com")
        assert result == mock_process
        mock_popen.assert_called_once()

class TestChromeBrowserName:
    """Test Chrome browser identification."""
    
    def test_chrome_browser_name_property(self):
        config = BrowserConfig(binary_path="/usr/bin/google-chrome", headless=False, user_data_dir=None, custom_flags=None)
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.browser_name == "chrome"
```

**Then implement**: `src/browser_launcher/browsers/chrome.py`

---

### Phase 3: Firefox Browser Implementation

#### Step 3.1: Write Firefox Tests

**File**: `tests/browsers/test_firefox.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.firefox import FirefoxLauncher
from browser_launcher.browsers.base import BrowserConfig

class TestFirefoxBuildCommandArgs:
    """Test Firefox argument building logic."""
    
    def test_firefox_command_includes_binary_path(self):
        config = BrowserConfig(binary_path="/usr/bin/firefox", headless=False, user_data_dir=None, custom_flags=None)
        browser = FirefoxLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[0] == "/usr/bin/firefox"
    
    def test_firefox_headless_adds_flag(self):
        config = BrowserConfig(binary_path="/usr/bin/firefox", headless=True, user_data_dir=None, custom_flags=None)
        browser = FirefoxLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "-headless" in args
    
    def test_firefox_no_headless_excludes_flag(self):
        config = BrowserConfig(binary_path="/usr/bin/firefox", headless=False, user_data_dir=None, custom_flags=None)
        browser = FirefoxLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "-headless" not in args
    
    def test_firefox_browser_name_property(self):
        config = BrowserConfig(binary_path="/usr/bin/firefox", headless=False, user_data_dir=None, custom_flags=None)
        browser = FirefoxLauncher(config, mock.Mock())
        assert browser.browser_name == "firefox"
    
    # Similar validation and launch tests as Chrome
```

**Then implement**: `src/browser_launcher/browsers/firefox.py`

---

### Phase 4: Safari Browser Implementation

#### Step 4.1: Write Safari Tests

**File**: `tests/browsers/test_safari.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.safari import SafariLauncher
from browser_launcher.browsers.base import BrowserConfig

class TestSafariBuildCommandArgs:
    """Test Safari argument building logic."""
    
    def test_safari_command_includes_binary_path(self):
        config = BrowserConfig(binary_path="/Applications/Safari.app/Contents/MacOS/Safari", headless=False, user_data_dir=None, custom_flags=None)
        browser = SafariLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[0] == "/Applications/Safari.app/Contents/MacOS/Safari"
    
    def test_safari_respects_opinionated_design(self):
        """Safari ignores headless flag - it doesn't support it."""
        config = BrowserConfig(binary_path="/Applications/Safari.app/Contents/MacOS/Safari", headless=True, user_data_dir=None, custom_flags=None)
        browser = SafariLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        # Safari should NOT add headless flag (it doesn't support it)
        assert "-headless" not in args
        assert "--headless" not in args
    
    def test_safari_ignores_user_data_dir(self):
        """Safari doesn't support user data directories."""
        config = BrowserConfig(binary_path="/Applications/Safari.app/Contents/MacOS/Safari", headless=False, user_data_dir="/tmp/profile", custom_flags=None)
        browser = SafariLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        # Safari should NOT have user-data-dir flag
        assert not any("user-data-dir" in arg for arg in args)
    
    def test_safari_browser_name_property(self):
        config = BrowserConfig(binary_path="/Applications/Safari.app/Contents/MacOS/Safari", headless=False, user_data_dir=None, custom_flags=None)
        browser = SafariLauncher(config, mock.Mock())
        assert browser.browser_name == "safari"
```

**Then implement**: `src/browser_launcher/browsers/safari.py`

---

### Phase 5: Edge Browser Implementation

#### Step 5.1: Write Edge Tests

**File**: `tests/browsers/test_edge.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.edge import EdgeLauncher
from browser_launcher.browsers.base import BrowserConfig

class TestEdgeBuildCommandArgs:
    """Test Edge argument building logic."""
    
    def test_edge_command_includes_binary_path(self):
        config = BrowserConfig(binary_path="/usr/bin/microsoft-edge", headless=False, user_data_dir=None, custom_flags=None)
        browser = EdgeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[0] == "/usr/bin/microsoft-edge"
    
    def test_edge_headless_adds_flag(self):
        config = BrowserConfig(binary_path="/usr/bin/microsoft-edge", headless=True, user_data_dir=None, custom_flags=None)
        browser = EdgeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--headless" in args
    
    def test_edge_browser_name_property(self):
        config = BrowserConfig(binary_path="/usr/bin/microsoft-edge", headless=False, user_data_dir=None, custom_flags=None)
        browser = EdgeLauncher(config, mock.Mock())
        assert browser.browser_name == "edge"
```

**Then implement**: `src/browser_launcher/browsers/edge.py`

---

### Phase 6: Factory Pattern

#### Step 6.1: Write Factory Tests

**File**: `tests/browsers/test_factory.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from browser_launcher.browsers.factory import BrowserFactory
from browser_launcher.browsers.base import BrowserConfig, BrowserLauncher

class TestBrowserFactory:
    """Test browser factory pattern."""
    
    def test_factory_creates_chrome_instance(self):
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        browser = BrowserFactory.create("chrome", config, mock.Mock())
        assert isinstance(browser, BrowserLauncher)
        assert browser.browser_name == "chrome"
    
    def test_factory_creates_firefox_instance(self):
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        browser = BrowserFactory.create("firefox", config, mock.Mock())
        assert isinstance(browser, BrowserLauncher)
        assert browser.browser_name == "firefox"
    
    def test_factory_creates_safari_instance(self):
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        browser = BrowserFactory.create("safari", config, mock.Mock())
        assert isinstance(browser, BrowserLauncher)
        assert browser.browser_name == "safari"
    
    def test_factory_creates_edge_instance(self):
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        browser = BrowserFactory.create("edge", config, mock.Mock())
        assert isinstance(browser, BrowserLauncher)
        assert browser.browser_name == "edge"
    
    def test_factory_raises_error_for_unsupported_browser(self):
        config = BrowserConfig(binary_path="/test", headless=False, user_data_dir=None, custom_flags=None)
        with pytest.raises(ValueError, match="Unsupported browser"):
            BrowserFactory.create("netscape", config, mock.Mock())
    
    def test_factory_get_available_browsers(self):
        available = BrowserFactory.get_available_browsers()
        assert "chrome" in available
        assert "firefox" in available
        assert "safari" in available
        assert "edge" in available
```

**Then implement**: `src/browser_launcher/browsers/factory.py`

---

### Phase 7: Configuration Management

#### Step 7.1: Write Config Tests

**File**: `tests/test_config.py` (write FIRST)

```python
import pytest
import tempfile
from pathlib import Path
from browser_launcher.config import BrowserLauncherConfig
from browser_launcher.browsers.base import BrowserConfig

class TestBrowserLauncherConfig:
    """Test configuration loading and management."""
    
    def test_config_loads_from_file(self):
        config_content = """
[general]
default_browser = "chrome"

[browsers.chrome]
binary_path = "/usr/bin/google-chrome"
headless = false
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config = BrowserLauncherConfig(Path(f.name))
            assert config.get_default_browser() == "chrome"
            Path(f.name).unlink()
    
    def test_config_get_browser_config_returns_browser_config(self):
        config = BrowserLauncherConfig()
        browser_config = config.get_browser_config("chrome", headless=False)
        assert isinstance(browser_config, BrowserConfig)
        assert browser_config.headless is False
    
    def test_config_headless_override(self):
        config = BrowserLauncherConfig()
        browser_config = config.get_browser_config("chrome", headless=True)
        assert browser_config.headless is True
    
    def test_config_get_default_url(self):
        config = BrowserLauncherConfig()
        url = config.get_default_url()
        assert isinstance(url, str)
        assert url.startswith("http")
```

**Then implement**: `src/browser_launcher/config.py`

---

### Phase 8: CLI Integration

#### Step 8.1: Write CLI Integration Tests

**File**: `tests/test_launch_integration.py` (write FIRST)

```python
import pytest
import unittest.mock as mock
from typer.testing import CliRunner
from browser_launcher.cli import app

class TestLaunchCommand:
    """Test launch CLI command integration."""
    
    @mock.patch('browser_launcher.cli.BrowserFactory.create')
    def test_launch_creates_browser_via_factory(self, mock_factory):
        runner = CliRunner()
        mock_browser = mock.Mock()
        mock_browser.validate_binary.return_value = True
        mock_browser.launch.return_value = mock.Mock()
        mock_factory.return_value = mock_browser
        
        with mock.patch('browser_launcher.cli.BrowserLauncherConfig'):
            result = runner.invoke(app, ['launch', 'https://example.com', '--browser', 'chrome'])
            assert result.exit_code == 0
            mock_factory.assert_called_once()
    
    @mock.patch('browser_launcher.cli.BrowserFactory.create')
    def test_launch_calls_browser_launch(self, mock_factory):
        runner = CliRunner()
        mock_browser = mock.Mock()
        mock_browser.validate_binary.return_value = True
        mock_browser.launch.return_value = mock.Mock()
        mock_factory.return_value = mock_browser
        
        with mock.patch('browser_launcher.cli.BrowserLauncherConfig'):
            result = runner.invoke(app, ['launch', 'https://example.com', '--browser', 'chrome'])
            mock_browser.launch.assert_called_once_with('https://example.com')
    
    @mock.patch('browser_launcher.cli.BrowserFactory.create')
    def test_launch_fails_if_binary_not_found(self, mock_factory):
        runner = CliRunner()
        mock_browser = mock.Mock()
        mock_browser.validate_binary.return_value = False
        mock_factory.return_value = mock_browser
        
        with mock.patch('browser_launcher.cli.BrowserLauncherConfig'):
            result = runner.invoke(app, ['launch', 'https://example.com', '--browser', 'chrome'])
            assert result.exit_code != 0
            assert "not found" in result.output.lower()
    
    @mock.patch('browser_launcher.cli.BrowserFactory.create')
    def test_launch_uses_default_browser_from_config(self, mock_factory):
        runner = CliRunner()
        mock_browser = mock.Mock()
        mock_browser.validate_binary.return_value = True
        mock_browser.launch.return_value = mock.Mock()
        mock_factory.return_value = mock_browser
        
        with mock.patch('browser_launcher.cli.BrowserLauncherConfig') as mock_config_class:
            mock_config = mock.Mock()
            mock_config.get_default_browser.return_value = "firefox"
            mock_config_class.return_value = mock_config
            
            result = runner.invoke(app, ['launch', 'https://example.com'])
            mock_config.get_default_browser.assert_called()
```

**Then update**: `src/browser_launcher/cli.py`

---

## Testing Strategy

### Five-Layer Testing Approach

#### Layer 1: Unit Tests (Browser Classes)
- **Goal**: Test each browser module in complete isolation without subprocess calls
- **Approach**: Mock subprocess + mock filesystem
- **Files**: `tests/browsers/test_*.py`

#### Layer 2: Factory Tests
- **Goal**: Verify factory correctly instantiates browsers and handles errors
- **Files**: `tests/browsers/test_factory.py`

#### Layer 3: Configuration Tests
- **Goal**: Test config loading, parsing, and browser-specific settings
- **Files**: `tests/test_config.py`

#### Layer 4: Integration Tests (CLI + Browsers)
- **Goal**: Test full flow from CLI to browser instantiation without actual launches
- **Files**: `tests/test_launch_integration.py`

#### Layer 5: Optional Real Browser Tests
- **Goal**: Real browser launches in controlled conditions
- **Marker**: `@pytest.mark.integration` - skipped in standard CI, run separately
- **Files**: `tests/integration/test_real_browser_launch.py`

### Test Organization

```
tests/
├── conftest.py                      # Shared fixtures
├── test_launch.py                   # Existing CLI tests (keep)
├── test_config.py                   # Config tests
├── test_launch_integration.py       # CLI + Factory integration
├── browsers/
│   ├── conftest.py                  # Browser-specific fixtures
│   ├── test_base.py                 # Base class contract tests
│   ├── test_chrome.py               # Chrome implementation tests
│   ├── test_firefox.py              # Firefox implementation tests
│   ├── test_safari.py               # Safari implementation tests
│   ├── test_edge.py                 # Edge implementation tests
│   └── test_factory.py              # Factory pattern tests
└── integration/
    └── test_real_browser_launch.py  # Real browser launches (optional)
```

### Mock Strategy

```python
# tests/conftest.py - shared fixtures
import pytest
import unittest.mock as mock

@pytest.fixture
def mock_subprocess():
    """Fixture providing mocked subprocess for browser tests."""
    with mock.patch('subprocess.Popen') as mock_popen:
        mock_process = mock.Mock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process
        yield mock_popen, mock_process

@pytest.fixture
def mock_logger():
    """Fixture providing mocked logger."""
    return mock.Mock()
```

### Running Tests

```bash
# Fast unit + integration tests
pytest tests/ -v

# Watch mode - runs tests on every file change
pytest-watch tests/ -c

# Run specific phase
pytest tests/browsers/test_chrome.py -v

# With coverage report
pytest --cov=browser_launcher tests/
```

### Coverage Goals

- **Base class**: 100% (abstract methods tested via implementations)
- **Browser implementations**: 90%+ (command-building logic fully tested)
- **Factory**: 100% (simple dispatcher)
- **Config**: 85%+ (file I/O partially mocked)
- **CLI**: 80%+ (integration focus, edge cases)

---

## TDD Execution Order

```
1. tests/browsers/test_base.py .............. Write base class contract tests
   ↓ Implement src/browser_launcher/browsers/base.py

2. tests/browsers/test_chrome.py ........... Write Chrome tests
   ↓ Implement src/browser_launcher/browsers/chrome.py

3. tests/browsers/test_firefox.py ......... Write Firefox tests
   ↓ Implement src/browser_launcher/browsers/firefox.py

4. tests/browsers/test_safari.py .......... Write Safari tests
   ↓ Implement src/browser_launcher/browsers/safari.py

5. tests/browsers/test_edge.py ............ Write Edge tests
   ↓ Implement src/browser_launcher/browsers/edge.py

6. tests/browsers/test_factory.py ......... Write factory tests
   ↓ Implement src/browser_launcher/browsers/factory.py

7. tests/test_config.py ................... Write config tests
   ↓ Implement src/browser_launcher/config.py

8. tests/test_launch_integration.py ....... Write CLI integration tests
   ↓ Update src/browser_launcher/cli.py

9. Run full test suite and verify coverage
```

---

## Error Handling Strategy

- **Binary validation**: Check if executable exists and is runnable
- **Configuration errors**: Clear messages if config is malformed
- **Launch failures**: Capture stderr/stdout for debugging
- **Graceful fallbacks**: Suggest alternatives if browser not found

---

## Extension Points

Future browsers can be added by:
1. Creating `browser/newbrowser.py` implementing `BrowserLauncher`
2. Registering in `BrowserFactory._browsers`
3. Adding config template section
4. No changes needed to CLI or other components

---

## Benefits of This Approach

✓ **Clear Requirements**: Tests define exactly what code must do  
✓ **Fewer Bugs**: Edge cases caught during test writing  
✓ **Better Design**: Forces thinking about interfaces before implementation  
✓ **Confident Refactoring**: Can refactor knowing tests will catch breakage  
✓ **Documentation**: Tests serve as usage examples  
✓ **Minimal Code**: Only implement what's needed to pass tests  
✓ **Easy to Extend**: New tests for new browsers follow existing patterns  
✓ **Speed**: Unit + integration tests run in seconds (mocked)  
✓ **Isolation**: Each browser tested independently  
✓ **CI-Friendly**: Fast tests run on every commit  

---

## Success Criteria

✓ Chrome, Firefox, Safari, Edge all launch with URLs
✓ Headless mode works where supported
✓ CLI properly delegates to browser implementations
✓ Configuration loads and applies correctly
✓ Error handling is clear and helpful
✓ New browsers can be added easily
✓ Tests pass for all browser modules
✓ Coverage meets 90%+ on critical components
✓ All 8 phases completed with passing tests
