import base64
import logging
import uuid
from datetime import date
from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException

# ruff: noqa: E501


logger = logging.getLogger(__name__)


class IDGenerator:
    """
    A generator for creating unique identifiers composed of:
    - A fixed 5-character UUID (per session)
    - The current date in YYYY-MM-DD format
    - A customizable prefix followed by an incrementing counter
    - An optional directory prepended to the output path

    Attributes:
        prefix (str): Custom string prefix for the identifier.
        counter (int): Internal counter that increments with each call.
        session_uuid (str): Fixed 5-character UUID for the session.
        directory (Path): Directory path prepended to the generated identifier.
    """

    def __init__(self, prefix: str = "foo", directory: str = "~/Downloads"):
        """
        Initialize the IDGenerator.

        Args:
            prefix (str): Prefix to use in the identifier. Defaults to "foo".
            directory (str): Directory to prepend to the identifier. Defaults to "~/Downloads".
        """
        self.prefix = prefix
        self.counter = 0
        self.session_uuid = uuid.uuid4().hex[:5]
        self.directory = Path(directory).expanduser()

    def generate(self) -> Path:
        """
        Generate a new identifier string.

        Returns:
            str: A string in the format '<directory>/<date>_<uuid>_<prefix><counter>.png'.
        """
        self.counter += 1
        today = date.today().isoformat()
        filename = f"{today}_{self.session_uuid}_{self.prefix}{self.counter}.png"
        return self.directory / filename


def _capture_screenshot(  # noqa: C901
    screenshot_path: Path, driver, delay: float = 0.5, **kwargs
) -> None:
    """
    Capture a screenshot using either the browser's native method or full-page emulation.

    Args:
        screenshot_path (Path): Path to save the screenshot.
        driver: Selenium WebDriver instance.
        delay (float): Optional delay before capturing. Defaults to 0.5 seconds.
        **kwargs: Optional parameters like 'extra_height' or 'extra_width' for full-page emulation.
    """
    # if not is_numeric(delay):
    #     print(f"delay should be numeric but type is: {type(delay)}; no screenshot taken")
    #     return

    sleep(delay)

    def send(cmd: str, params: dict) -> dict:
        """Send a Chrome DevTools Protocol command."""
        return driver.execute_cdp_cmd(cmd, params)

    def evaluate(script: str):
        """Evaluate a JavaScript expression in the browser context with retries."""
        for _ in range(3):
            response = send(
                "Runtime.evaluate", {"returnByValue": True, "expression": script}
            )
            if response and "value" in response.get("result", {}):
                return response["result"]["value"]
            sleep(2.0)
        return None

    def full(**kwargs):
        """Capture a full-page screenshot using emulated device metrics."""
        extra_height = (
            f", {kwargs.pop('extra_height')}" if "extra_height" in kwargs else ""
        )
        extra_width = (
            f", {kwargs.pop('extra_width')}" if "extra_width" in kwargs else ""
        )

        # is_mobile = str2bool(evaluate("typeof window.orientation !== 'undefined'"))
        is_mobile = False
        restore = None

        if is_mobile:
            restore = evaluate(
                "({"
                "width: window.innerWidth,"
                "height: innerHeight,"
                "deviceScaleFactor: window.devicePixelRatio || 1,"
                "mobile: typeof window.orientation !== 'undefined'"
                "})"
            )

        metrics = evaluate(
            "({"
            f"width: Math.max(window.innerWidth, document.body.scrollWidth, document.documentElement.scrollWidth{extra_width})|0,"
            f"height: Math.max(innerHeight, document.body.scrollHeight, document.documentElement.scrollHeight{extra_height})|0,"
            "deviceScaleFactor: window.devicePixelRatio || 1,"
            "mobile: typeof window.orientation !== 'undefined'"
            "})"
        )

        if metrics is None:
            logger.warning("Falling back to normal screenshot")
            safe_window()
            return

        send("Emulation.setDeviceMetricsOverride", metrics)
        screenshot = send(
            "Page.captureScreenshot", {"format": "png", "fromSurface": True}
        )

        if is_mobile and restore:
            send("Emulation.setDeviceMetricsOverride", restore)
        else:
            send("Emulation.clearDeviceMetricsOverride", {})

        png = base64.b64decode(screenshot["data"])
        with open(screenshot_path, "wb") as fh:
            fh.write(png)

    def window():
        """Capture a standard viewport screenshot."""
        driver.save_screenshot(screenshot_path.as_posix())

    def safe_window():
        """Safely attempt a standard screenshot with exception handling."""
        try:
            window()
        except InvalidSessionIdException:
            logger.error("InvalidSessionIdException caught in safe_window")
        except Exception as e:
            logger.error(f"Unexpected {type(e)} caught in safe_window")

    try:
        if isinstance(driver, webdriver.Chrome) or isinstance(driver, webdriver.Edge):
            full(**kwargs)
        elif isinstance(driver, webdriver.Firefox):
            driver.get_full_page_screenshot_as_file(str(screenshot_path))
        else:
            driver.save_screenshot(str(screenshot_path))

        logger.info(f"Captured {screenshot_path}")
    except InvalidSessionIdException as e:
        logger.error(
            "session has gone bad, you need to relaunch to be able"
            f" to capture screenshot {type(e)}"
        )
        raise
    except NoSuchWindowException as e:
        logger.error(
            "session has gone bad, you need to relaunch to be able"
            f"to capture screenshot {type(e)}"
        )
        raise
    except Exception as e:
        logger.error(
            "session has gone bad, you need to relaunch to be able"
            f"to capture screenshot {type(e)} {e!r}"
        )
        raise e
