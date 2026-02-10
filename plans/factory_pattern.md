# Factory Pattern Implementation Plan

## Objective
Implement a `BrowserFactory` in `src/browser_launcher/browsers/factory.py` to centralize browser instantiation, following the architecture in [`plans/IMPLEMENTATION_PLAN.md`](plans/IMPLEMENTATION_PLAN.md).

## Steps

1. **Define Factory Class**
   - Create `BrowserFactory` with a mapping of browser names to launcher classes.
   - Implement `create(browser_name, config, logger)` to instantiate the correct launcher.
   - Implement `get_available_browsers()` to list supported browsers.

2. **Integrate with CLI**
   - Refactor CLI to use the factory for browser instantiation.
   - Remove direct references to browser classes from CLI.

3. **Extensibility**
   - Document how to add new browsers to the factory.

## Example Implementation
```python
from typing import Type
from browser_launcher.browsers.base import BrowserLauncher, BrowserConfig
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.firefox import FirefoxLauncher
# from browser_launcher.browsers.safari import SafariLauncher
# from browser_launcher.browsers.edge import EdgeLauncher

class BrowserFactory:
    """Factory for creating browser launcher instances."""
    _browsers = {
        "chrome": ChromeLauncher,
        "firefox": FirefoxLauncher,
        # "safari": SafariLauncher,
        # "edge": EdgeLauncher,
    }

    @classmethod
    def create(cls, browser_name: str, config: BrowserConfig, logger) -> BrowserLauncher:
        if browser_name not in cls._browsers:
            raise ValueError(f"Unsupported browser: {browser_name}")
        browser_class: Type[BrowserLauncher] = cls._browsers[browser_name]
        return browser_class(config, logger)

    @classmethod
    def get_available_browsers(cls):
        return list(cls._browsers.keys())
```

## Next Steps
- Implement this pattern in code mode.
- Update CLI to use the factory for all browser launches.
