"""
Tests for the screenshot module.

This module contains unit tests for the IDGenerator class and
_capture_screenshot function.
"""

import base64
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException

from browser_launcher.screenshot import IDGenerator, _capture_screenshot


class TestIDGenerator:
    """Test suite for the IDGenerator class."""

    def test_init_default_values(self) -> None:
        """Test IDGenerator initialization with default values."""
        generator = IDGenerator()
        assert generator.prefix == "foo"
        assert generator.counter == 0
        assert generator.directory == Path.home() / "Downloads"
        assert len(generator.session_uuid) == 5

    def test_init_custom_prefix(self) -> None:
        """Test IDGenerator initialization with custom prefix."""
        generator = IDGenerator(prefix="custom")
        assert generator.prefix == "custom"

    def test_init_custom_directory(self, tmp_path: Path) -> None:
        """Test IDGenerator initialization with custom directory."""
        generator = IDGenerator(directory=str(tmp_path))
        assert generator.directory == tmp_path

    def test_init_tilde_expansion(self, monkeypatch) -> None:
        """Test that tilde (~) is expanded to home directory."""
        generator = IDGenerator(directory="~/custom")
        expected = Path.home() / "custom"
        assert generator.directory == expected

    def test_generate_returns_path(self) -> None:
        """Test that generate() returns a Path object."""
        generator = IDGenerator()
        result = generator.generate()
        assert isinstance(result, Path)

    def test_generate_increments_counter(self) -> None:
        """Test that counter increments with each generate() call."""
        generator = IDGenerator()
        assert generator.counter == 0
        generator.generate()
        assert generator.counter == 1
        generator.generate()
        assert generator.counter == 2

    def test_generate_filename_format(self, tmp_path: Path) -> None:
        """Test that generated filename follows the correct format."""
        generator = IDGenerator(prefix="snap", directory=str(tmp_path))
        path = generator.generate()

        filename = path.name
        # Format: {date}_{uuid}_{prefix}{counter}.png
        parts = filename.rsplit(".", 1)
        assert len(parts) == 2
        assert parts[1] == "png"

        name_parts = parts[0].split("_")
        assert len(name_parts) == 3

        # Check date format (YYYY-MM-DD)
        today = date.today().isoformat()
        assert name_parts[0] == today

        # Check session uuid (5 chars)
        assert len(name_parts[1]) == 5

        # Check prefix and counter (snap1, snap2, etc.)
        assert name_parts[2].startswith("snap")
        assert name_parts[2][4:] == "1"

    def test_generate_uses_correct_directory(self, tmp_path: Path) -> None:
        """Test that generated path is in the specified directory."""
        generator = IDGenerator(directory=str(tmp_path))
        path = generator.generate()
        assert path.parent == tmp_path

    def test_generate_multiple_calls_have_different_counters(
        self, tmp_path: Path
    ) -> None:
        """Test that multiple generate() calls create different filenames."""
        generator = IDGenerator(directory=str(tmp_path))
        path1 = generator.generate()
        path2 = generator.generate()
        path3 = generator.generate()

        assert path1.name != path2.name
        assert path2.name != path3.name
        assert path1.name != path3.name

    def test_generate_multiple_calls_have_same_session_uuid(
        self, tmp_path: Path
    ) -> None:
        """Test that session_uuid stays consistent across generate() calls."""
        generator = IDGenerator(directory=str(tmp_path))
        path1 = generator.generate()
        path2 = generator.generate()

        # Extract session UUID from filenames
        uuid1 = path1.name.split("_")[1]
        uuid2 = path2.name.split("_")[1]

        assert uuid1 == uuid2


class TestCaptureScreenshot:
    """Test suite for the _capture_screenshot function."""

    def test_capture_screenshot_chrome_driver(self, tmp_path: Path) -> None:
        """Test screenshot capture with Chrome WebDriver."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Mock the CDP command responses
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # First evaluate call returns None (is_mobile)
            {
                "result": {
                    "value": {
                        "width": 1920,
                        "height": 1080,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    }
                }
            },  # metrics
            {"data": base64.b64encode(b"fake_png_data").decode()},  # captureScreenshot
        ]

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver, delay=0.5)

        # Verify execute_cdp_cmd was called
        assert mock_driver.execute_cdp_cmd.called

    def test_capture_screenshot_edge_driver(self, tmp_path: Path) -> None:
        """Test screenshot capture with Edge WebDriver."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Edge)

        # Mock the CDP command responses
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {
                "result": {
                    "value": {
                        "width": 1920,
                        "height": 1080,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    }
                }
            },  # metrics
            {"data": base64.b64encode(b"fake_png_data").decode()},  # captureScreenshot
        ]

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        assert mock_driver.execute_cdp_cmd.called

    def test_capture_screenshot_firefox_driver(self, tmp_path: Path) -> None:
        """Test screenshot capture with Firefox WebDriver."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Firefox)

        with mock.patch("browser_launcher.screenshot.sleep"):
            _capture_screenshot(screenshot_path, mock_driver)

        # Verify Firefox's native method was called
        mock_driver.get_full_page_screenshot_as_file.assert_called_once_with(
            str(screenshot_path)
        )

    def test_capture_screenshot_safari_driver(self, tmp_path: Path) -> None:
        """
        Test screenshot capture with Safari WebDriver (fallback to
        save_screenshot).
        """
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Safari)

        with mock.patch("browser_launcher.screenshot.sleep"):
            _capture_screenshot(screenshot_path, mock_driver)

        # Verify fallback method was called
        mock_driver.save_screenshot.assert_called_once_with(str(screenshot_path))

    def test_capture_screenshot_delay_parameter(self, tmp_path: Path) -> None:
        """Test that the delay parameter is passed to sleep()."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Safari)

        with mock.patch("browser_launcher.screenshot.sleep") as mock_sleep:
            _capture_screenshot(screenshot_path, mock_driver, delay=2.5)

        # Verify sleep was called with the correct delay
        mock_sleep.assert_called_with(2.5)

    def test_capture_screenshot_default_delay(self, tmp_path: Path) -> None:
        """Test that the default delay is 0.5 seconds."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Safari)

        with mock.patch("browser_launcher.screenshot.sleep") as mock_sleep:
            _capture_screenshot(screenshot_path, mock_driver)

        # Verify sleep was called at least once with default delay (0.5)
        assert mock_sleep.called
        # Check first call with default delay
        assert mock_sleep.call_args_list[0][0][0] == 0.5

    def test_capture_screenshot_chrome_fallback_on_metrics_none(
        self, tmp_path: Path
    ) -> None:
        """
        Test Chrome fallback to normal screenshot when metrics evaluation
        returns None.
        """
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Mock metrics evaluation to return None (fallback scenario)
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {"result": {}},  # metrics returns empty (None case)
        ]

        with mock.patch("builtins.print") as mock_print:
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        # Verify fallback message was printed
        mock_print.assert_called_with("Falling back to normal screenshot")
        # Verify save_screenshot was called as fallback
        mock_driver.save_screenshot.assert_called()

    def test_capture_screenshot_invalid_session_exception(self, tmp_path: Path) -> None:
        """Test that InvalidSessionIdException is re-raised."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)
        mock_driver.execute_cdp_cmd.side_effect = InvalidSessionIdException(
            "Session invalid"
        )

        with mock.patch("browser_launcher.screenshot.sleep"):
            with pytest.raises(InvalidSessionIdException):
                _capture_screenshot(screenshot_path, mock_driver)

    def test_capture_screenshot_no_such_window_exception(self, tmp_path: Path) -> None:
        """Test that NoSuchWindowException is re-raised."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)
        mock_driver.execute_cdp_cmd.side_effect = NoSuchWindowException(
            "Window not found"
        )

        with mock.patch("browser_launcher.screenshot.sleep"):
            with pytest.raises(NoSuchWindowException):
                _capture_screenshot(screenshot_path, mock_driver)

    def test_capture_screenshot_generic_exception(self, tmp_path: Path) -> None:
        """Test that generic exceptions are re-raised."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)
        mock_driver.execute_cdp_cmd.side_effect = RuntimeError("Unexpected error")

        with mock.patch("browser_launcher.screenshot.sleep"):
            with pytest.raises(RuntimeError):
                _capture_screenshot(screenshot_path, mock_driver)

    def test_capture_screenshot_safe_window_invalid_session_exception(
        self, tmp_path: Path
    ) -> None:
        """Test safe_window handling of InvalidSessionIdException during fallback."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # First call fails, triggering fallback to safe_window
        mock_driver.execute_cdp_cmd.side_effect = InvalidSessionIdException(
            "Session invalid"
        )

        with mock.patch("browser_launcher.screenshot.sleep"):
            with pytest.raises(InvalidSessionIdException):
                _capture_screenshot(screenshot_path, mock_driver)

    def test_capture_screenshot_with_extra_height_kwarg(self, tmp_path: Path) -> None:
        """Test that extra_height kwarg is passed to full() screenshot method."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Mock CDP command responses
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {
                "result": {
                    "value": {
                        "width": 1920,
                        "height": 1080,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    }
                }
            },  # metrics
            {"data": base64.b64encode(b"fake_png_data").decode()},  # captureScreenshot
        ]

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver, extra_height=100)

        # Should successfully handle the extra_height parameter
        assert mock_driver.execute_cdp_cmd.called

    def test_capture_screenshot_with_extra_width_kwarg(self, tmp_path: Path) -> None:
        """Test that extra_width kwarg is passed to full() screenshot method."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Mock CDP command responses
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {
                "result": {
                    "value": {
                        "width": 1920,
                        "height": 1080,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    }
                }
            },  # metrics
            {"data": base64.b64encode(b"fake_png_data").decode()},  # captureScreenshot
        ]

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver, extra_width=100)

        # Should successfully handle the extra_width parameter
        assert mock_driver.execute_cdp_cmd.called

    @pytest.mark.parametrize(
        "driver_spec",
        [
            webdriver.Chrome,
            webdriver.Edge,
        ],
    )
    def test_capture_screenshot_cdp_browsers(self, tmp_path: Path, driver_spec) -> None:
        """Test that Chrome and Edge use CDP commands for screenshot."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=driver_spec)

        # Mock CDP responses
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {
                "result": {
                    "value": {
                        "width": 1920,
                        "height": 1080,
                        "deviceScaleFactor": 1,
                        "mobile": False,
                    }
                }
            },  # metrics
            {"data": base64.b64encode(b"fake_png_data").decode()},  # captureScreenshot
        ]

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        # Verify execute_cdp_cmd was called (uses CDP for Chrome and Edge)
        assert mock_driver.execute_cdp_cmd.called

    def test_capture_screenshot_chrome_full_path_success(self, tmp_path: Path) -> None:
        """Test Chrome screenshot capture with successful full-page method."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Create PNG data
        png_data = b"\x89PNG\r\n\x1a\n"
        encoded_data = base64.b64encode(png_data).decode()

        # Track how many times execute_cdp_cmd is called
        call_count = [0]

        def cdp_side_effect(cmd, params):
            call_count[0] += 1
            if cmd == "Runtime.evaluate":
                return {
                    "result": {
                        "value": {
                            "width": 1920,
                            "height": 1080,
                            "deviceScaleFactor": 1,
                            "mobile": False,
                        }
                        if call_count[0] == 2
                        else None
                    }
                }
            elif cmd == "Emulation.setDeviceMetricsOverride":
                return {}
            elif cmd == "Emulation.clearDeviceMetricsOverride":
                return {}
            elif cmd == "Page.captureScreenshot":
                return {"data": encoded_data}
            return {}

        mock_driver.execute_cdp_cmd.side_effect = cdp_side_effect

        with mock.patch("builtins.open", mock.mock_open()):
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        # Verify that execute_cdp_cmd was called for full-page screenshot
        assert mock_driver.execute_cdp_cmd.called

    def test_capture_screenshot_safe_window_prints_on_invalid_session(
        self, tmp_path: Path
    ) -> None:
        """Test that InvalidSessionIdException in safe_window is caught and printed."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Make save_screenshot raise InvalidSessionIdException
        mock_driver.save_screenshot.side_effect = InvalidSessionIdException("Invalid")
        # Metrics fails, triggering fallback to safe_window
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {"result": {}},  # metrics returns empty - triggers fallback
        ]

        with mock.patch("builtins.print") as mock_print:
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        # Verify fallback message and exception message were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Falling back" in str(call) for call in print_calls)

    def test_capture_screenshot_safe_window_prints_on_generic_exception(
        self, tmp_path: Path
    ) -> None:
        """Test that generic exceptions in safe_window are caught and printed."""
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Chrome)

        # Make save_screenshot raise a generic exception
        mock_driver.save_screenshot.side_effect = ValueError("Some error")
        # Metrics fails, triggering fallback to safe_window
        mock_driver.execute_cdp_cmd.side_effect = [
            {"result": {"value": None}},  # is_mobile
            {"result": {}},  # metrics returns empty - triggers fallback
        ]

        with mock.patch("builtins.print") as mock_print:
            with mock.patch("browser_launcher.screenshot.sleep"):
                _capture_screenshot(screenshot_path, mock_driver)

        # Verify unexpected exception message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Unexpected" in str(call) for call in print_calls)

    def test_capture_screenshot_window_function_called_on_safari(
        self, tmp_path: Path
    ) -> None:
        """
        Test that the window function is called for non-Chrome/Edge/Firefox
        drivers.
        """
        screenshot_path = tmp_path / "screenshot.png"
        mock_driver = mock.Mock(spec=webdriver.Safari)

        with mock.patch("browser_launcher.screenshot.sleep"):
            _capture_screenshot(screenshot_path, mock_driver)

        # Verify the window() function is called by checking save_screenshot
        mock_driver.save_screenshot.assert_called_once_with(str(screenshot_path))
