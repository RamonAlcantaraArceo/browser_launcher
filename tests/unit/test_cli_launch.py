from unittest.mock import MagicMock, PropertyMock, call, mock_open, patch

import pytest
from typer.testing import CliRunner

from browser_launcher.browsers.base import BrowserConfig
from browser_launcher.cli import app, cache_cookies_for_session
from browser_launcher.cookies import CookieConfig

runner = CliRunner()


@pytest.mark.unit
def test_launch_success(monkeypatch):
    # Mock config loader
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"

    # Mock browser factory and browser instance
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()

    # Patch dependencies
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code == 0
    assert "Launching chrome at http://example.com" in result.output
    mock_bl.launch.assert_called_once_with(url="http://example.com")
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_with_url_and_browser(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://default.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers",
        lambda: ["chrome", "firefox"],
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch", "http://custom.com", "--browser", "firefox"])
    assert result.exit_code == 0
    assert "Launching firefox at http://custom.com" in result.output
    mock_bl.launch.assert_called_once_with(url="http://custom.com")
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_with_headless(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=True,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch", "--headless"])
    assert result.exit_code == 0
    mock_config.get_browser_config.assert_called_once_with("chrome", headless=True)
    mock_bl.launch.assert_called_once()
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_with_verbose_and_debug(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: True
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch", "--verbose", "--debug"])
    assert result.exit_code == 0
    mock_bl.launch.assert_called_once()
    mock_bl.driver.close.assert_called()
    # Accept the actual log message format
    mock_logger.info.assert_any_call(
        "Starting browser launch - [launch] headless=False | user=default | "
        "env=prod | verbose=True | debug=True"
    )


@pytest.mark.unit
def test_launch_config_file_not_found(monkeypatch):
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig",
        lambda: (_ for _ in ()).throw(FileNotFoundError("no config")),
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code != 0
    assert "Error:" in result.output
    mock_logger.error.assert_called()


@pytest.mark.unit
def test_launch_unsupported_browser(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "opera"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
    mock_config.get_default_url.return_value = "http://example.com"
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers",
        lambda: ["chrome", "firefox"],
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code != 0
    assert "Unsupported browser" in result.output
    mock_logger.error.assert_called()


@pytest.mark.unit
def test_launch_browser_config_load_failure(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.side_effect = Exception("bad config")
    mock_config.get_default_url.return_value = "http://example.com"
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code != 0
    assert "Error loading browser config" in result.output
    mock_logger.error.assert_called()


@pytest.mark.unit
def test_launch_browser_instantiation_failure(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create",
        lambda *a, **kw: (_ for _ in ()).throw(Exception("fail create")),
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code != 0
    assert "Error instantiating browser" in result.output
    mock_logger.error.assert_called()


@pytest.mark.unit
def test_launch_browser_launch_failure(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch.side_effect = Exception("fail launch")
    mock_logger = MagicMock(info=MagicMock(), error=MagicMock())
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code != 0
    assert "Error launching browser" in result.output
    mock_logger.error.assert_called()


@pytest.mark.unit
def test_launch_session_gone_bad(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    # session_id is None on first read, then not None
    type(mock_bl.driver).session_id = property(lambda self: None)
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )
    # Simulate one loop with session_id None, then exit
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code == 0
    assert "session has gone bad" in result.output
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_eoferror(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    type(mock_bl.driver).session_id = PropertyMock(side_effect=EOFError("foo"))
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )

    result = runner.invoke(app, ["launch"], input=None)
    assert result.exit_code == 0
    assert "Exiting..." in result.output
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_driver_close_exception(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close.side_effect = Exception("close fail")
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_current_logger",
        lambda: MagicMock(info=MagicMock(), error=MagicMock()),
    )
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])
    assert result.exit_code == 0
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_console_logging_config(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    # Test both True and False for console_logging
    for val in (True, False):
        monkeypatch.setattr(
            "browser_launcher.cli.get_console_logging_setting", lambda: val
        )
        monkeypatch.setattr(
            "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
        )
        monkeypatch.setattr(
            "browser_launcher.cli.get_current_logger",
            lambda: MagicMock(info=MagicMock(), error=MagicMock()),
        )
        monkeypatch.setattr(
            "sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""]))
        )
        result = runner.invoke(app, ["launch"])
        assert result.exit_code == 0
        mock_bl.launch.assert_called()
        mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_logger_not_initialized(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "http://example.com"
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: MagicMock()
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    # Mock get_current_logger to return None
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: None)
    # with pytest.raises(RuntimeError, match="Logger was not initialized correctly."):
    result = runner.invoke(app, ["launch"])
    assert result.exit_code == 1
    assert "Logger was not initialized correctly." in result.output


@pytest.mark.unit
def test_launch_with_locale(monkeypatch):
    """Test that the locale parameter is correctly set on the browser config."""
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    # Create a BrowserConfig that we can verify gets the locale set
    browser_config = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_browser_config.return_value = browser_config
    mock_config.get_default_url.return_value = "http://example.com"

    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()

    mock_logger = MagicMock(info=MagicMock(), error=MagicMock(), debug=MagicMock())

    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    # Test with custom locale
    result = runner.invoke(app, ["launch", "--locale", "fr-FR"])
    assert result.exit_code == 0

    # Verify the locale was set on the browser config
    assert browser_config.locale == "fr-FR"

    # Verify the debug log was called
    mock_logger.debug.assert_any_call("Set browser locale to: fr-FR")
    mock_bl.launch.assert_called_once()
    mock_bl.driver.close.assert_called()


@pytest.mark.unit
def test_launch_with_default_locale(monkeypatch):
    """Test that the default locale is used when no locale parameter is provided."""
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    # Create a BrowserConfig that should keep its default locale
    browser_config = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_browser_config.return_value = browser_config
    mock_config.get_default_url.return_value = "http://example.com"

    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()

    mock_logger = MagicMock(info=MagicMock(), error=MagicMock(), debug=MagicMock())

    monkeypatch.setattr(
        "browser_launcher.cli.BrowserLauncherConfig", lambda: mock_config
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.get_available_browsers", lambda: ["chrome"]
    )
    monkeypatch.setattr(
        "browser_launcher.cli.BrowserFactory.create", lambda *a, **kw: mock_bl
    )
    monkeypatch.setattr(
        "browser_launcher.cli.get_console_logging_setting", lambda: False
    )
    monkeypatch.setattr(
        "browser_launcher.cli.initialize_logging", lambda *a, **kw: None
    )
    monkeypatch.setattr("browser_launcher.cli.get_current_logger", lambda: mock_logger)
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    # Test without locale parameter (should use default "en-US")
    result = runner.invoke(app, ["launch"])
    assert result.exit_code == 0

    # Verify the default locale is used
    assert browser_config.locale == "en-US"

    # Verify the debug log WAS called with the default locale
    mock_logger.debug.assert_any_call("Set browser locale to: en-US")
    mock_bl.launch.assert_called_once()
    mock_bl.driver.close.assert_called()


# Tests for cache_cookies_for_session function


@pytest.mark.unit
def test_cache_cookies_for_session_success():
    """Test successful cookie caching with valid cookies."""
    # Setup mocks
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    # Setup cookie config data
    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {
                    "cookies": {
                        "sessionid": {"domain": "example.com"},
                        "authtoken": {"domain": "api.example.com"},
                    }
                }
            }
        }
    }

    # Setup cookie config
    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = cookie_config_data
    mock_cookie_config.update_cookie_cache = MagicMock()

    # Mock browser cookies returned from read_cookies_from_browser
    mock_browser_cookies = [
        {"name": "sessionid", "value": "abc123", "domain": "example.com"},
        {"name": "authtoken", "value": "def456", "domain": "api.example.com"},
        {
            "name": "other_cookie",
            "value": "xyz789",
            "domain": "example.com",
        },  # Should be filtered out
    ]

    with (
        patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies,
        patch("browser_launcher.cli.get_home_directory") as mock_get_home,
        patch("browser_launcher.cli.tomli_w.dump") as mock_dump,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        mock_read_cookies.return_value = mock_browser_cookies
        mock_get_home.return_value.joinpath.return_value = "/fake/config.toml"

        # Call the function
        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify cookies were read from browser for both domains
        expected_calls = [
            call(mock_driver, "example.com"),
            call(mock_driver, "api.example.com"),
        ]
        mock_read_cookies.assert_has_calls(expected_calls, any_order=True)

        # Verify cache was updated for both valid cookies
        mock_cookie_config.update_cookie_cache.assert_has_calls(
            [
                call("testuser", "testenv", "example.com", "sessionid", "abc123"),
                call("testuser", "testenv", "api.example.com", "authtoken", "def456"),
            ],
            any_order=True,
        )

        # Verify config was saved to file
        mock_file.assert_called_once()
        mock_dump.assert_called_once_with(cookie_config_data, mock_file().__enter__())

        # Verify success messages
        success_call = mock_console.print.call_args_list[-1][0][
            0
        ]  # Last console.print call
        assert "✅ Cached 2 cookies for testuser/testenv/" in success_call
        assert "api.example.com" in success_call
        assert "example.com" in success_call

        # Verify logging messages (order independent)
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        read_log = next(
            call for call in log_calls if "Read 2 cookies from browser" in call
        )
        assert "testuser/testenv:" in read_log
        assert "api.example.com" in read_log
        assert "example.com" in read_log


@pytest.mark.unit
def test_cache_cookies_for_session_no_cookie_config():
    """Test error handling when CookieConfig is None."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {"cookies": {"sessionid": {"domain": "example.com"}}}
            }
        }
    }

    mock_browser_cookies = [
        {"name": "sessionid", "value": "abc123", "domain": "example.com"}
    ]

    with patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies:
        mock_read_cookies.return_value = mock_browser_cookies

        # Call with None cookie_config
        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            None,  # CookieConfig is None
            mock_logger,
            mock_console,
        )

        # Verify error logging and console output
        mock_logger.error.assert_called_with(
            "CookieConfig is not initialized, cannot update cache"
        )
        mock_console.print.assert_called_with(
            "❌ [red]Error:[/red] CookieConfig is not initialized, cannot update cache"
        )


@pytest.mark.unit
def test_cache_cookies_for_session_no_cookies_found():
    """Test handling when no target cookies are found in browser."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {"cookies": {"sessionid": {"domain": "example.com"}}}
            }
        }
    }

    # Return cookies that don't match target cookies
    mock_browser_cookies = [
        {"name": "other_cookie", "value": "xyz789", "domain": "example.com"}
    ]

    mock_cookie_config = MagicMock(spec=CookieConfig)

    with patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies:
        mock_read_cookies.return_value = mock_browser_cookies

        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify warning messages when no cookies found
        mock_console.print.assert_called_with(
            "⚠️ No cookies found for domain example.com"
        )
        mock_logger.debug.assert_called_with(
            "⚠️ No cookies found for domain example.com"
        )


@pytest.mark.unit
def test_cache_cookies_for_session_read_cookies_exception():
    """Test error handling when reading cookies from browser fails."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {"cookies": {"sessionid": {"domain": "example.com"}}}
            }
        }
    }

    mock_cookie_config = MagicMock(spec=CookieConfig)

    with patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies:
        # Simulate exception when reading cookies
        mock_read_cookies.side_effect = Exception("Driver error")

        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify error handling
        mock_console.print.assert_called_with("❌ Error caching cookies: Driver error")
        mock_logger.error.assert_called_with(
            "Error caching cookies: Driver error", exc_info=True
        )


@pytest.mark.unit
def test_cache_cookies_for_session_file_write_exception():
    """Test error handling when saving config file fails."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {"cookies": {"sessionid": {"domain": "example.com"}}}
            }
        }
    }

    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = cookie_config_data

    mock_browser_cookies = [
        {"name": "sessionid", "value": "abc123", "domain": "example.com"}
    ]

    with (
        patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies,
        patch("browser_launcher.cli.get_home_directory") as mock_get_home,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        mock_read_cookies.return_value = mock_browser_cookies
        mock_get_home.return_value.joinpath.return_value = "/fake/config.toml"

        # Simulate file write error
        mock_file.side_effect = PermissionError("Permission denied")

        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify error handling
        mock_console.print.assert_called_with(
            "❌ Error caching cookies: Permission denied"
        )
        mock_logger.error.assert_called_with(
            "Error caching cookies: Permission denied", exc_info=True
        )


@pytest.mark.unit
def test_cache_cookies_for_session_multiple_domains():
    """Test caching cookies from multiple domains."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    # Setup with multiple domains
    cookie_config_data = {
        "users": {
            "testuser": {
                "testenv": {
                    "cookies": {
                        "auth": {"domain": "auth.example.com"},
                        "session": {"domain": "app.example.com"},
                        "token": {"domain": "api.example.com"},
                    }
                }
            }
        }
    }

    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = cookie_config_data

    # Mock cookies from different domains
    def mock_read_cookies_side_effect(driver, domain):
        if domain == "auth.example.com":
            return [{"name": "auth", "value": "auth123", "domain": "auth.example.com"}]
        elif domain == "app.example.com":
            return [
                {"name": "session", "value": "sess456", "domain": "app.example.com"}
            ]
        elif domain == "api.example.com":
            return [{"name": "token", "value": "tok789", "domain": "api.example.com"}]
        return []

    with (
        patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies,
        patch("browser_launcher.cli.get_home_directory") as mock_get_home,
        patch("browser_launcher.cli.tomli_w.dump"),
        patch("builtins.open", mock_open()),
    ):
        mock_read_cookies.side_effect = mock_read_cookies_side_effect
        mock_get_home.return_value.joinpath.return_value = "/fake/config.toml"

        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            None,  # domain is None, should work with multiple domains
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify cookies were read from all three domains
        assert mock_read_cookies.call_count == 3
        expected_domains = {"auth.example.com", "app.example.com", "api.example.com"}
        called_domains = {call[0][1] for call in mock_read_cookies.call_args_list}
        assert called_domains == expected_domains

        # Verify all three cookies were cached
        assert mock_cookie_config.update_cookie_cache.call_count == 3

        # Verify success message includes all domains
        success_call = mock_console.print.call_args_list[-1][0][
            0
        ]  # Last console.print call
        assert "✅ Cached 3 cookies for testuser/testenv/" in success_call


@pytest.mark.unit
def test_cache_cookies_for_session_duplicate_cookie_names():
    """Test handling of duplicate cookie names from different domains."""
    mock_browser_controller = MagicMock()
    mock_driver = MagicMock()
    mock_browser_controller.driver = mock_driver

    mock_logger = MagicMock()
    mock_console = MagicMock()

    cookie_config_data = {
        "users": {
            "testuser": {"testenv": {"cookies": {"session": {"domain": "example.com"}}}}
        }
    }

    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = cookie_config_data

    # Return multiple cookies with same name (should only keep first one)
    mock_browser_cookies = [
        {"name": "session", "value": "first", "domain": "example.com"},
        {"name": "session", "value": "second", "domain": "example.com"},  # Duplicate
    ]

    with (
        patch("browser_launcher.cli.read_cookies_from_browser") as mock_read_cookies,
        patch("browser_launcher.cli.get_home_directory") as mock_get_home,
        patch("browser_launcher.cli.tomli_w.dump"),
        patch("builtins.open", mock_open()),
    ):
        mock_read_cookies.return_value = mock_browser_cookies
        mock_get_home.return_value.joinpath.return_value = "/fake/config.toml"

        cache_cookies_for_session(
            mock_browser_controller,
            "testuser",
            "testenv",
            "example.com",
            cookie_config_data,
            mock_cookie_config,
            mock_logger,
            mock_console,
        )

        # Verify only one cookie was cached (first occurrence)
        mock_cookie_config.update_cookie_cache.assert_called_once_with(
            "testuser", "testenv", "example.com", "session", "first"
        )

        # Verify success message shows only 1 cookie
        success_call = mock_console.print.call_args_list[-1][0][0]
        assert "✅ Cached 1 cookies for" in success_call
