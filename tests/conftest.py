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
def allure_markers(request: pytest.FixtureRequest):
    """Automatically add test markers to Allure reports."""

    # Add test markers
    for marker in request.node.iter_markers():
        if marker.name in ("unit", "smoke"):
            allure.feature(marker.name.capitalize())


@pytest.fixture(autouse=True)
def allure_python_version_metadata(request: pytest.FixtureRequest) -> None:
    """
    Configure Allure metadata for test execution based on Python version
    and module hierarchy.

    This fixture automatically attaches metadata to each test in Allure reports:
    - Python version (from ALLURE_PYTHON_VERSION env var or current interpreter)
    - Parent suite derived from test file path structure
    - Suite labeled with Python version
    - Sub-suite based on the test module name

    The parent suite is constructed from the directory hierarchy following the 'tests'
    directory in the test file path, enabling organized test grouping in Allure reports.

    Args:
        request: pytest request fixture providing access to test node information

    Returns:
        None

    Raises:
        AttributeError: If allure.dynamic methods are unavailable
        (gracefully handled with hasattr checks)

    Environment Variables:
        ALLURE_PYTHON_VERSION: Optional override for Python version label
        (defaults to major.minor format)

    Example:
        For a test at path 'tests/functional/auth/test_login.py':
        - parent_suite: 'functional.auth'
        - suite: 'Python 3.14'
        - sub_suite: 'test_login'
    """

    # Determine Python version label
    python_version = os.getenv(
        "ALLURE_PYTHON_VERSION", f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    label = f"Python {python_version}"

    # Extract module name from request
    module_name = "unknown_module"
    if hasattr(request, "node") and hasattr(request.node, "module"):
        module_name = request.node.module.__name__.split(".")[-1]

    # Set Python version parameter
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "parameter"):
        allure.dynamic.parameter("python_version", label)

    # Set parent suite based on test file path
    if (
        hasattr(allure, "dynamic")
        and hasattr(allure.dynamic, "parent_suite")
        and hasattr(request.node, "fspath")
    ):
        test_path = Path(str(request.node.fspath))
        # Extract the desired grouping from the test path for parent_suite
        # by joining parts after 'tests' directory
        if "tests" in test_path.parts:
            tests_idx = test_path.parts.index("tests")
            if len(test_path.parts) > tests_idx + 1:
                allure.dynamic.parent_suite(
                    ".".join(test_path.parts[tests_idx + 1 : -1])
                )
    else:
        # Fallback parent suite if dynamic methods are unavailable
        allure.dynamic.parent_suite("misc")

    # Set suite based on Python version
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "suite"):
        allure.dynamic.suite(label)

    # Set sub-suite based on module name
    if hasattr(allure, "dynamic") and hasattr(allure.dynamic, "sub_suite"):
        allure.dynamic.sub_suite(module_name)


def pytest_addoption(parser):
    parser.addini(
        "allure_always_capture_selenium_logs",
        "Always capture Selenium logs for Allure (true/false/always/yes/1)",
        default="false",
    )
    parser.addoption(
        "--allure-always-capture-selenium-logs",
        action="store",
        default=None,
        help="Always capture Selenium logs for Allure (true/false/always/yes/1)",
    )


@pytest.fixture(autouse=True)
def capture_selenium_logs_on_failure(request: pytest.FixtureRequest, tmp_path: Path):  # noqa: C901
    """Capture and attach Selenium logs to Allure report on test failure,
    or always if configured."""
    log_patterns = ["*driver.log"]

    # Clean up any existing log files before the test runs
    for pattern in log_patterns:
        for log_file in tmp_path.glob(pattern):
            if log_file.is_file():
                try:
                    log_file.unlink()
                except Exception:
                    pass

    yield

    # Priority: env var > CLI option > pytest.ini
    always_capture = request.config.getoption(
        "--allure-always-capture-selenium-logs"
    ) or request.config.getini("allure_always_capture_selenium_logs")
    always_capture = str(always_capture).lower() in ("1", "true", "yes", "always")
    test_failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

    if test_failed or always_capture:
        if test_failed:
            allure.attach(
                "Test failed during call phase",
                name="Test Failure",
                attachment_type=allure.attachment_type.TEXT,
            )

        # Try to capture logs from the test
        if hasattr(request, "node") and hasattr(request.node, "_obj"):
            # Attach driver logs if present
            project_root = tmp_path

            for pattern in log_patterns:
                for log_file in project_root.glob(pattern):
                    if log_file.is_file():
                        try:
                            with open(log_file, "r") as f:
                                log_content = f.read()
                                allure.attach(
                                    log_content,
                                    name=log_file.name,
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
