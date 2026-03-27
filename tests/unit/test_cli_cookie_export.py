"""Unit tests for clipboard cookie export helpers in cli.py."""

from unittest.mock import MagicMock

import pytest

from browser_launcher.cli import (
    _build_playwright_cookie_export_script,
    _copy_text_to_clipboard_macos,
    export_all_cookies_to_clipboard,
)


@pytest.mark.unit
def test_build_playwright_cookie_export_script_deterministic_and_optional_fields():
    cookies = [
        {
            "name": "z_cookie",
            "value": "zzz",
            "domain": "www.deptagency.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax",
            "expiry": 2000,
        },
        {
            "name": "a_cookie",
            "value": "a\"quote",
            "domain": "www.deptagency.com",
            "path": "/foo",
            "secure": False,
        },
    ]

    script = _build_playwright_cookie_export_script(cookies)

    assert script.startswith("async (page) => {")
    assert "await page.context().addCookies([" in script
    assert "await page.reload();" in script
    # Sorted by cookie name to keep output deterministic
    assert script.find("name: \"a_cookie\"") < script.find("name: \"z_cookie\"")
    # Optional fields omitted when missing
    assert "sameSite" in script
    assert "expiry" in script
    assert "path: \"/foo\"" in script
    # Verify quote escaping in values
    assert 'value: "a\\"quote"' in script


@pytest.mark.unit
def test_copy_text_to_clipboard_macos_calls_pbcopy(monkeypatch):
    called = {}

    def _mock_run(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs

    monkeypatch.setattr("browser_launcher.cli.subprocess.run", _mock_run)

    _copy_text_to_clipboard_macos("hello")

    assert called["args"][0] == ["pbcopy"]
    assert called["kwargs"]["input"] == "hello"
    assert called["kwargs"]["text"] is True
    assert called["kwargs"]["check"] is True


@pytest.mark.unit
def test_export_all_cookies_to_clipboard_success(monkeypatch):
    driver = MagicMock()
    driver.get_cookies.return_value = [
        {
            "name": "session_id",
            "value": "abc123",
            "domain": "www.deptagency.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
        }
    ]
    logger = MagicMock()
    console = MagicMock()

    copied = {"text": None}

    def _mock_copy(text):
        copied["text"] = text

    monkeypatch.setattr(
        "browser_launcher.cli._copy_text_to_clipboard_macos",
        _mock_copy,
    )

    export_all_cookies_to_clipboard(driver, logger, console)

    assert copied["text"] is not None
    assert "session_id" in copied["text"]
    console.print.assert_called_with(
        "✅ Copied Playwright cookie export script with 1 cookies to clipboard"
    )


@pytest.mark.unit
def test_export_all_cookies_to_clipboard_no_cookies(monkeypatch):
    driver = MagicMock()
    driver.get_cookies.return_value = []
    logger = MagicMock()
    console = MagicMock()

    mock_copy = MagicMock()
    monkeypatch.setattr("browser_launcher.cli._copy_text_to_clipboard_macos", mock_copy)

    export_all_cookies_to_clipboard(driver, logger, console)

    mock_copy.assert_not_called()
    console.print.assert_called_with("⚠️ No cookies found in current browser session")


@pytest.mark.unit
def test_export_all_cookies_to_clipboard_handles_copy_error(monkeypatch):
    driver = MagicMock()
    driver.get_cookies.return_value = [{"name": "n", "value": "v"}]
    logger = MagicMock()
    console = MagicMock()

    def _mock_copy(_text):
        raise RuntimeError("copy failed")

    monkeypatch.setattr(
        "browser_launcher.cli._copy_text_to_clipboard_macos",
        _mock_copy,
    )

    export_all_cookies_to_clipboard(driver, logger, console)

    assert "Error copying cookie export to clipboard: copy failed" in str(
        console.print.call_args_list[-1][0][0]
    )


@pytest.mark.unit
def test_export_all_cookies_to_clipboard_handles_read_error():
    driver = MagicMock()
    driver.get_cookies.side_effect = RuntimeError("read failed")
    logger = MagicMock()
    console = MagicMock()

    export_all_cookies_to_clipboard(driver, logger, console)

    assert "Error reading cookies from browser: read failed" in str(
        console.print.call_args_list[-1][0][0]
    )
