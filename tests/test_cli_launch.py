from unittest.mock import MagicMock, PropertyMock

from typer.testing import CliRunner

from browser_launcher.cli import app

runner = CliRunner()


def test_launch_success(monkeypatch):
    # Mock config loader
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_with_url_and_browser(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_with_headless(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_with_verbose_and_debug(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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
        "Starting browser launch - [launch] headless=False | user=default | env=prod | verbose=True | debug=True"
    )


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


def test_launch_browser_instantiation_failure(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_browser_launch_failure(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_session_gone_bad(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_eoferror(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_driver_close_exception(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_console_logging_config(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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


def test_launch_logger_not_initialized(monkeypatch):
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = {"foo": "bar"}
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
