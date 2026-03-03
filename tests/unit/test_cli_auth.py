from unittest.mock import MagicMock, call

import pytest
from typer.testing import CliRunner

from browser_launcher.auth.config import AuthConfig
from browser_launcher.auth.result import AuthResult
from browser_launcher.browsers.base import BrowserConfig
from browser_launcher.cli import app
from browser_launcher.cookies import CookieConfig

runner = CliRunner()


@pytest.mark.unit
def test_attempt_authentication_returns_cached_and_skips_module(monkeypatch):
    """Cached valid cookies should bypass authenticator module execution."""
    mock_browser_controller = MagicMock()
    mock_config_loader = MagicMock()
    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_logger = MagicMock()
    mock_console = MagicMock()

    injected = [{"name": "session_id", "value": "cached", "domain": "example.com"}]

    monkeypatch.setattr(
        "browser_launcher.cli.inject_and_verify_cookies",
        lambda *a, **kw: injected,
    )

    mock_auth_factory_create = MagicMock()
    monkeypatch.setattr(
        "browser_launcher.cli.AuthFactory.create", mock_auth_factory_create
    )

    from browser_launcher.cli import attempt_authentication

    result = attempt_authentication(
        browser_controller=mock_browser_controller,
        config_loader=mock_config_loader,
        cookie_config=mock_cookie_config,
        user="default",
        env="prod",
        domain="example.com",
        launch_url="https://example.com",
        logger=mock_logger,
        console=mock_console,
    )

    assert result == injected
    mock_auth_factory_create.assert_not_called()


@pytest.mark.unit
def test_attempt_authentication_uses_module_and_saves_cookies(monkeypatch):
    """When cache is empty, authenticator module is executed and cookies are cached."""
    mock_browser_controller = MagicMock()
    mock_browser_controller.driver = MagicMock()
    mock_config_loader = MagicMock()
    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = {"users": {}}
    mock_logger = MagicMock()
    mock_console = MagicMock()

    monkeypatch.setattr(
        "browser_launcher.cli.inject_and_verify_cookies", lambda *a, **kw: None
    )

    mock_config_loader.get_available_auth_modules.return_value = {"form_auth": {}}
    mock_config_loader.get_auth_config.return_value = AuthConfig(
        retry_attempts=1,
        credentials={"username": "alice", "password": "secret"},
    )

    auth_result = AuthResult(
        success=True,
        cookies=[
            {"name": "session_id", "value": "abc123", "domain": "example.com"},
            {"name": "csrf", "value": "xyz789", "domain": "example.com"},
        ],
    )
    mock_authenticator = MagicMock()
    mock_authenticator.authenticate.return_value = auth_result

    monkeypatch.setattr(
        "browser_launcher.cli.AuthFactory.create", lambda *a, **kw: mock_authenticator
    )

    from browser_launcher.cli import attempt_authentication

    result = attempt_authentication(
        browser_controller=mock_browser_controller,
        config_loader=mock_config_loader,
        cookie_config=mock_cookie_config,
        user="default",
        env="prod",
        domain="example.com",
        launch_url="https://example.com",
        logger=mock_logger,
        console=mock_console,
    )

    assert result == auth_result.cookies
    mock_authenticator.authenticate.assert_called_once_with("https://example.com")
    assert mock_cookie_config.update_cookie_cache.call_count == 2
    mock_cookie_config.update_cookie_cache.assert_has_calls(
        [
            call("default", "prod", "example.com", "session_id", "abc123"),
            call("default", "prod", "example.com", "csrf", "xyz789"),
        ],
        any_order=True,
    )
    mock_cookie_config.persist_to_file.assert_called_once()


@pytest.mark.unit
def test_attempt_authentication_retries_with_prompted_credentials(monkeypatch):
    """Authentication retries should prompt for updated credentials and retry."""
    mock_browser_controller = MagicMock()
    mock_config_loader = MagicMock()
    mock_cookie_config = MagicMock(spec=CookieConfig)
    mock_cookie_config.config_data = {"users": {}}
    mock_logger = MagicMock()
    mock_console = MagicMock()

    monkeypatch.setattr(
        "browser_launcher.cli.inject_and_verify_cookies", lambda *a, **kw: None
    )

    auth_config = AuthConfig(
        retry_attempts=2,
        credentials={"username": "alice", "password": "wrong"},
    )
    mock_config_loader.get_available_auth_modules.return_value = {"form_auth": {}}
    mock_config_loader.get_auth_config.return_value = auth_config

    mock_authenticator = MagicMock()
    mock_authenticator.authenticate.side_effect = [
        Exception("invalid credentials"),
        AuthResult(
            success=True,
            cookies=[{"name": "session_id", "value": "ok", "domain": "example.com"}],
        ),
    ]
    monkeypatch.setattr(
        "browser_launcher.cli.AuthFactory.create", lambda *a, **kw: mock_authenticator
    )

    monkeypatch.setattr("browser_launcher.cli.typer.confirm", lambda *a, **kw: True)

    prompt_values = {"username": "bob", "password": "new-secret"}

    def _mock_prompt(text, **kwargs):
        lowered = str(text).lower()
        for key, value in prompt_values.items():
            if key in lowered:
                return value
        return ""

    monkeypatch.setattr("browser_launcher.cli.typer.prompt", _mock_prompt)

    from browser_launcher.cli import attempt_authentication

    result = attempt_authentication(
        browser_controller=mock_browser_controller,
        config_loader=mock_config_loader,
        cookie_config=mock_cookie_config,
        user="default",
        env="prod",
        domain="example.com",
        launch_url="https://example.com",
        logger=mock_logger,
        console=mock_console,
    )

    assert result == [{"name": "session_id", "value": "ok", "domain": "example.com"}]
    assert auth_config.credentials["username"] == "bob"
    assert auth_config.credentials["password"] == "new-secret"
    assert mock_authenticator.authenticate.call_count == 2


@pytest.mark.unit
def test_launch_calls_attempt_authentication_hook(monkeypatch):
    """launch command should invoke authentication hook after browser launch."""
    mock_config = MagicMock()
    mock_config.get_default_browser.return_value = "chrome"
    mock_config.get_browser_config.return_value = BrowserConfig(
        binary_path=None,
        headless=False,
        user_data_dir=None,
        custom_flags=None,
    )
    mock_config.get_default_url.return_value = "https://example.com"
    mock_config.config_data = {
        "users": {
            "default": {
                "prod": {
                    "cookies": {
                        "session_id": {
                            "domain": "example.com",
                            "value": "...",
                            "timestamp": "...",
                        }
                    }
                }
            }
        }
    }

    mock_bl = MagicMock()
    mock_bl.driver.session_id = "abc"
    mock_bl.driver.close = MagicMock()
    mock_bl.launch = MagicMock()

    mock_attempt_authentication = MagicMock(return_value=None)

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
        lambda: MagicMock(
            info=MagicMock(), error=MagicMock(), warning=MagicMock(), debug=MagicMock()
        ),
    )
    monkeypatch.setattr(
        "browser_launcher.cli.attempt_authentication", mock_attempt_authentication
    )
    monkeypatch.setattr("sys.stdin", MagicMock(read=MagicMock(side_effect=["x", ""])))

    result = runner.invoke(app, ["launch"])

    assert result.exit_code == 0
    mock_attempt_authentication.assert_called_once()
