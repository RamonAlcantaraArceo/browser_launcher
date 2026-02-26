# Extra Options Support - Architecture Enhancement

## Overview

The BrowserConfig now includes an `extra_options` dictionary that allows users to pass arbitrary browser-specific options that may not be explicitly supported yet.

## Use Cases

### Chrome Mobile Emulation
```python
config = BrowserConfig(
    binary_path="/usr/bin/google-chrome",
    headless=False,
    user_data_dir=None,
    custom_flags=None,
    extra_options={
        "device": "Pixel 5",
        "orientation": "portrait",
        "mobileEmulation": {
            "deviceName": "Pixel 5"
        }
    }
)
```

### Chrome Experimental Options
```python
config = BrowserConfig(
    binary_path="/usr/bin/google-chrome",
    headless=False,
    user_data_dir=None,
    custom_flags=None,
    extra_options={
        "prefs": {
            "intl.accept_languages": "es-ES",
            "profile.default_content_settings.popups": 0
        }
    }
)
```

### Future Browser-Specific Features
Any new browser-specific settings can be added via `extra_options` without modifying the codebase:

```python
config = BrowserConfig(
    binary_path="/usr/bin/firefox",
    headless=False,
    user_data_dir=None,
    custom_flags=None,
    extra_options={
        "addon_context_menu": True,
        "extensions": ["path/to/addon.xpi"]
    }
)
```

## Implementation Details

### BrowserConfig
- Added `extra_options: Dict[str, Any]` with default empty dict
- Default is initialized via `field(default_factory=dict)` to avoid mutable default issues
- Type hints allow `Any` for maximum flexibility

### Browser Implementations
Each browser implementation can access `self.config.extra_options` to:
1. Log available options
2. Handle browser-specific option processing
3. Pass options to subprocess or browser control libraries (e.g., Selenium)

### Backward Compatibility
- Existing code without `extra_options` continues to work
- The field is optional - callers don't need to provide it
- Default empty dict means no extra options if not specified

## Philosophy

**Progressive Enhancement**: Start with common options (headless, flags, user_data_dir) that all browsers support, but allow power users to pass browser-specific options they know about without waiting for explicit implementation.

This keeps the library:
- **Simple**: Core functionality is straightforward
- **Extensible**: Users can experiment with new options immediately
- **Documented**: Users document what works in their configuration/docs
- **Future-proof**: No need to update the library for new browser options

## Example: Adding locale support to Chrome later

```python
# User can do this TODAY with extra_options:
config = BrowserConfig(
    binary_path="/usr/bin/google-chrome",
    headless=False,
    user_data_dir=None,
    custom_flags=None,
    extra_options={
        "prefs": {"intl.accept_languages": "es-ES"}
    }
)

# Later, if we add explicit locale support:
config = BrowserConfig(
    binary_path="/usr/bin/google-chrome",
    headless=False,
    user_data_dir=None,
    custom_flags=None,
    locale="es-ES"  # New field
)
# extra_options would still be available for other advanced options
```

## All Tests Passing ✓

- 11 base class tests: PASS
- 14 Chrome tests: PASS
- **Total: 25/25 PASS**

The addition of `extra_options` is backward compatible and doesn't break any existing tests.
