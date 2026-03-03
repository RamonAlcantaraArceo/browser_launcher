"""Tests for authentication retry handler."""

from unittest.mock import MagicMock

import pytest

from browser_launcher.auth.config import AuthConfig


@pytest.mark.unit
def test_retry_handler_initialization():
    """AuthRetryHandler should initialize with config and console."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=3, retry_delay_seconds=1.5)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    assert handler.config == config
    assert handler.console == console
    assert handler.logger == logger
    assert handler.current_attempt == 0


@pytest.mark.unit
def test_should_retry_returns_false_when_max_attempts_reached():
    """should_retry should return False when max attempts reached."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=2)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)
    handler.current_attempt = 3  # Already at max (retry_attempts + 1)

    result = handler.should_retry(error_message="Authentication failed")

    assert result is False
    console.print.assert_not_called()


@pytest.mark.unit
def test_should_retry_prompts_user_and_returns_true_on_confirm(monkeypatch):
    """should_retry should prompt user and return True when user confirms."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=3)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)
    handler.current_attempt = 1

    # Mock typer.confirm to return True
    monkeypatch.setattr(
        "browser_launcher.auth.retry.typer.confirm", lambda *a, **kw: True
    )

    result = handler.should_retry(error_message="Invalid credentials")

    assert result is True
    # Should print error message
    assert console.print.called


@pytest.mark.unit
def test_should_retry_returns_false_when_user_declines(monkeypatch):
    """should_retry should return False when user declines retry."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=3)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)
    handler.current_attempt = 1

    # Mock typer.confirm to return False
    monkeypatch.setattr(
        "browser_launcher.auth.retry.typer.confirm", lambda *a, **kw: False
    )

    result = handler.should_retry(error_message="Invalid credentials")

    assert result is False
    assert console.print.called


@pytest.mark.unit
def test_prompt_for_credentials_updates_all_credentials(monkeypatch):
    """prompt_for_credentials should prompt for each credential key."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(
        credentials={
            "username": "old_user",
            "password": "old_pass",
            "token": "old_token",
        }
    )
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    # Mock typer.prompt to return different values
    def mock_prompt(text, **kwargs):
        if "username" in str(text).lower():
            return "new_user"
        elif "password" in str(text).lower():
            return "new_pass"
        elif "token" in str(text).lower():
            return "new_token"
        return ""

    monkeypatch.setattr("browser_launcher.auth.retry.typer.prompt", mock_prompt)

    updated = handler.prompt_for_credentials()

    assert updated["username"] == "new_user"
    assert updated["password"] == "new_pass"
    assert updated["token"] == "new_token"


@pytest.mark.unit
def test_prompt_for_credentials_hides_sensitive_fields(monkeypatch):
    """prompt_for_credentials should hide input for password/token fields."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(
        credentials={"username": "alice", "password": "secret", "api_token": "xyz"}
    )
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    prompt_calls = []

    def mock_prompt(text, **kwargs):
        prompt_calls.append((text, kwargs))
        return "value"

    monkeypatch.setattr("browser_launcher.auth.retry.typer.prompt", mock_prompt)

    handler.prompt_for_credentials()

    # Check that password and token use hide_input=True
    for text, kwargs in prompt_calls:
        text_lower = str(text).lower()
        if "password" in text_lower or "token" in text_lower:
            assert kwargs.get("hide_input") is True
        else:
            assert kwargs.get("hide_input") is False


@pytest.mark.unit
def test_increment_attempt_increases_counter():
    """increment_attempt should increase the current attempt counter."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=3)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    assert handler.current_attempt == 0
    handler.increment_attempt()
    assert handler.current_attempt == 1
    handler.increment_attempt()
    assert handler.current_attempt == 2


@pytest.mark.unit
def test_get_remaining_attempts():
    """get_remaining_attempts should return correct count."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=3)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    # Total attempts = retry_attempts + 1 = 4
    assert handler.get_remaining_attempts() == 4

    handler.current_attempt = 1
    assert handler.get_remaining_attempts() == 3

    handler.current_attempt = 4
    assert handler.get_remaining_attempts() == 0


@pytest.mark.unit
def test_display_error_message_uses_rich_console():
    """display_error_message should format error with Rich console."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig()
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)

    handler.display_error_message("Authentication failed", attempt=1, total=3)

    console.print.assert_called_once()
    call_args = console.print.call_args[0][0]
    assert "Authentication failed" in call_args
    assert "1" in call_args or "3" in call_args


@pytest.mark.unit
def test_should_retry_with_delay(monkeypatch):
    """should_retry should apply retry delay from config."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=2, retry_delay_seconds=0.1)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)
    handler.current_attempt = 1

    monkeypatch.setattr(
        "browser_launcher.auth.retry.typer.confirm", lambda *a, **kw: True
    )

    mock_sleep = MagicMock()
    monkeypatch.setattr("time.sleep", mock_sleep)

    handler.should_retry(error_message="Failed", apply_delay=True)

    mock_sleep.assert_called_once_with(0.1)


@pytest.mark.unit
def test_should_retry_skips_delay_when_not_requested(monkeypatch):
    """should_retry should skip delay when apply_delay=False."""
    from browser_launcher.auth.retry import AuthRetryHandler

    config = AuthConfig(retry_attempts=2, retry_delay_seconds=0.5)
    console = MagicMock()
    logger = MagicMock()

    handler = AuthRetryHandler(config=config, console=console, logger=logger)
    handler.current_attempt = 1

    monkeypatch.setattr(
        "browser_launcher.auth.retry.typer.confirm", lambda *a, **kw: True
    )

    mock_sleep = MagicMock()
    monkeypatch.setattr("time.sleep", mock_sleep)

    handler.should_retry(error_message="Failed", apply_delay=False)

    mock_sleep.assert_not_called()
