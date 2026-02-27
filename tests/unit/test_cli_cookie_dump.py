"""Unit tests for cookie dump helpers in cli.py."""

from unittest.mock import MagicMock

import pytest
from rich.console import Console

from browser_launcher.cookies import _dump_cookies_from_browser, _format_cookie_expiry


@pytest.mark.unit
def test_format_cookie_expiry_relative_units(monkeypatch):
    monkeypatch.setattr("browser_launcher.cookies.time.time", lambda: 1000)

    assert _format_cookie_expiry(None) == "session"
    assert _format_cookie_expiry("bad") == "invalid"
    assert _format_cookie_expiry(999) == "expired"
    assert _format_cookie_expiry(1045) == "+45s"
    assert _format_cookie_expiry(1061) == "+1m"
    assert _format_cookie_expiry(4601) == "+1h"
    assert _format_cookie_expiry(173801) == "+2d"


@pytest.mark.unit
def test_dump_cookies_uses_current_url_domain_and_renders_cookie_fields(monkeypatch):

    def _mock_read_cookies(driver, domain):
        return [
            {
                "name": "zeta_cookie",
                "value": "zxy123456",
                "domain": "example.com",
                "path": "/",
                "secure": False,
                "httpOnly": False,
                "sameSite": "Strict",
                "expiry": 1234567999,
            },
            {
                "name": "session_id",
                "value": "abcdef123456",
                "domain": "example.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "Lax",
                "expiry": 1234567890,
            },
            {
                "name": "alpha_cookie",
                "value": "alpha123456",
                "domain": "example.com",
                "path": "/",
                "secure": True,
                "httpOnly": False,
                "sameSite": "None",
                "expiry": 1234567000,
            },
        ]

    monkeypatch.setattr(
        "browser_launcher.cookies.read_cookies_from_browser", _mock_read_cookies
    )
    monkeypatch.setattr(
        "browser_launcher.cookies._format_cookie_expiry", lambda _: "+2h"
    )

    driver = MagicMock()
    driver.current_url = "https://example.com/dashboard"
    logger = MagicMock()
    console = Console(record=True, width=200)

    _dump_cookies_from_browser(driver, logger, console)

    output = console.export_text()
    alpha_pos = output.find("alpha_cookie")
    session_pos = output.find("session_id")
    zeta_pos = output.find("zeta_cookie")

    assert alpha_pos != -1
    assert session_pos != -1
    assert zeta_pos != -1
    assert alpha_pos < session_pos < zeta_pos
    assert "session_id" in output
    assert "alpha1..." in output
    assert "abcdef..." in output
    assert "zxy123..." in output
    assert "example.com" in output
    assert "/" in output
    assert "│ 1 │" in output
    assert "│ 2 │" in output
    assert "│ 3 │" in output
    assert "yes" in output
    assert "Lax" in output
    assert "+2h" in output
