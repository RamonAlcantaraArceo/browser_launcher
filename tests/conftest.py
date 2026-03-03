"""Shared pytest fixtures for browser_launcher tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import allure
import pytest
import toml

from browser_launcher.browsers.base import BrowserConfig


@pytest.fixture(autouse=True)
def allure_markers(request):
    """Automatically add test markers to Allure reports."""

    # Add test markers
    for marker in request.node.iter_markers():
        if marker.name in ("unit", "smoke"):
            allure.feature(marker.name.capitalize())


@pytest.fixture(autouse=True)
def allure_python_version_metadata(request):
    """Add Python-version metadata to each test in Allure reports."""

    python_version = os.getenv(
        "ALLURE_PYTHON_VERSION", f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    label = f"Python {python_version}"
    module_name = "unknown_module"
    if hasattr(request, "node") and hasattr(request.node, "module"):
        module_name = request.node.module.__name__.split(".")[-1]

    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "parameter"):
        allure.dynamic.parameter("python_version", label)
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "parent_suite"):
        allure.dynamic.parent_suite("tests.unit")
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "suite"):
        allure.dynamic.suite(label)
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "sub_suite"):
        allure.dynamic.sub_suite(module_name)


@pytest.fixture(autouse=True)
def capture_selenium_logs_on_failure(request):
    """Capture and attach Selenium logs to Allure report on test failure."""
    yield

    # Check if test failed
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        # Attach failure information
        allure.attach(
            "Test failed during call phase",
            name="Test Failure",
            attachment_type=allure.attachment_type.TEXT,
        )

        # Try to capture logs from the test
        if hasattr(request, "node") and hasattr(request.node, "_obj"):
            try:
                test_instance = request.node._obj()
                if hasattr(test_instance, "driver") or hasattr(
                    test_instance, "browser_controller"
                ):
                    allure.attach(
                        "Selenium driver was active during test failure",
                        name="Driver Status",
                        attachment_type=allure.attachment_type.TEXT,
                    )
            except Exception:
                pass


@pytest.fixture
def allure_environment_properties():
    """Set up Allure environment properties."""

    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "environment"):
        allure.dynamic.environment(
            Python="3.10+", PyTest=pytest.__version__, OS="macOS/Linux/Windows"
        )
    elif hasattr(allure, "environment"):
        allure.environment(
            Python="3.10+", PyTest=pytest.__version__, OS="macOS/Linux/Windows"
        )
    # else: skip setting environment if not available


@pytest.fixture
def mock_browser_config():
    """Mock BrowserLauncherConfig using real default_config.toml content."""
    # Load the actual default config
    default_config_path = (
        Path(__file__).parent.parent
        / "src"
        / "browser_launcher"
        / "assets"
        / "default_config.toml"
    )
    config_data = toml.load(default_config_path)

    with patch("browser_launcher.cli.BrowserLauncherConfig") as mock_config:
        config_instance = MagicMock()
        config_instance.config_data = config_data
        config_instance.get_default_browser.return_value = config_data["general"][
            "default_browser"
        ]
        config_instance.get_default_url.return_value = config_data["urls"]["homepage"]
        config_instance.get_console_logging.return_value = config_data["logging"][
            "console_logging"
        ]
        config_instance.get_logging_level.return_value = config_data["logging"][
            "default_log_level"
        ]

        # Mock get_browser_config to return a valid BrowserConfig
        def mock_get_browser_config(browser_name: str, headless: bool = False):
            browser_data = config_data.get("browsers", {}).get(browser_name, {})
            return BrowserConfig(
                binary_path=None,
                headless=headless or browser_data.get("headless", False),
                user_data_dir=None,
                custom_flags=None,
                extra_options={},
            )

        config_instance.get_browser_config.side_effect = mock_get_browser_config

        mock_config.return_value = config_instance
        yield config_instance


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test result for later use in fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# Automatically assign Allure feature labels based on test file path
_FEATURE_LABELS = {
    "config": "Config",
    "cookies": "Cookies",
    "cli": "CLI",
    "utils": "Utils",
    "auth": "Auth",
    "browsers": "Browsers",
}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):

    path = Path(str(item.fspath))
    try:
        parts = path.parts
        # Find the index of 'unit' in the path
        if "unit" in parts or "smoke" in parts:
            unit_idx = parts.index("unit") if "unit" in parts else parts.index("smoke")

            # item.add_marker(
            #     allure.story("Unit Tests" if "unit" in parts else "Smoke Tests")
            # )

            # The next part is the feature directory
            if len(parts) > unit_idx + 1:
                feature_dir = parts[unit_idx + 1]
                feature_label = _FEATURE_LABELS.get(feature_dir)
                if feature_label:
                    item.add_marker(allure.feature(feature_label))

                file_name = path.stem
                if feature_label is None:
                    feature_labels = [
                        _FEATURE_LABELS[key]
                        for key in _FEATURE_LABELS.keys()
                        if key in file_name
                    ]
                    if feature_labels:
                        for feature_label in feature_labels:
                            item.add_marker(allure.feature(feature_label))

                if not any(
                    "feature" in marker.kwargs.values()
                    for marker in item.iter_markers()
                ):
                    item.add_marker(allure.feature("Misc"))

    except Exception:
        pass
