import pytest
from browser_launcher.browsers.factory import BrowserFactory
from browser_launcher.browsers.base import BrowserConfig

class DummyLogger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

@pytest.mark.parametrize("browser_name,expected_class", [
    ("chrome", "ChromeLauncher"),
    ("firefox", "FirefoxLauncher"),
    ("safari", "SafariLauncher"),
    ("edge", "EdgeLauncher"),
])
def test_factory_creates_supported_browsers(browser_name, expected_class):
    config = BrowserConfig(
        binary_path=None,
        headless=True,
        user_data_dir=None,
        custom_flags=None,
        extra_options={}
    )
    logger = DummyLogger()
    launcher = BrowserFactory.create(browser_name, config, logger)
    assert launcher.__class__.__name__ == expected_class
    assert launcher.config == config
    assert hasattr(launcher, "launch")


def test_factory_raises_for_unsupported_browser():
    config = BrowserConfig(
        binary_path=None,
        headless=True,
        user_data_dir=None,
        custom_flags=None,
        extra_options={}
    )
    logger = DummyLogger()
    with pytest.raises(ValueError):
        BrowserFactory.create("opera", config, logger)


def test_get_available_browsers_lists_all():
    browsers = BrowserFactory.get_available_browsers()
    assert set(browsers) == {"chrome", "firefox", "safari", "edge"}
