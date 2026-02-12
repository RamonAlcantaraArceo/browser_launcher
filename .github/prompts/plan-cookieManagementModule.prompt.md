# Plan: Cookie Management Module with TDD

**TL;DR** Create a new `cookies.py` module that manages bidirectional cookie synchronization with configuration-driven rules. The module will support hierarchical configuration (users → environments → domains), cache cookies in TOML with 8-hour TTL, and integrate into the browser launch flow via a hook after initial navigation. Implementation uses TDD with unit tests for each component before writing implementation code.

## Steps

### 1. Define data structures & configuration schema ([src/browser_launcher/cookies.py](src/browser_launcher/cookies.py))
   - Create `CookieRule` dataclass: domain, name, browser-specific variants, TTL override
   - Create `CacheEntry` dataclass: value, timestamp, expiry logic
   - Create `CookieConfig` class: load hierarchical structure from config
   - Update [config.py](src/browser_launcher/config.py) to parse new `[users]` section with `[users.{user}.{env}.{domain}]` structure
   - Support cookie rule format: `cookies = [{name = "session_id", variants = {firefox = "sess_id"}}]`

### 2. Implement core cookie operations ([src/browser_launcher/cookies.py](src/browser_launcher/cookies.py))
   - `read_cookies_from_browser(driver, domain)` → Extract cookies matching domain from Selenium driver
   - `write_cookies_to_browser(driver, cookies: List[dict], domain)` → Inject cookies into browser via driver.add_cookie()
   - `is_cookie_valid(cache_entry: CacheEntry, ttl_seconds=28800)` → Check if cached cookie is within TTL (default 8 hours)
   - `get_applicable_rules(domain, user, env)` → Query hierarchical config for matching rules

### 3. Implement cache management ([src/browser_launcher/cookies.py](src/browser_launcher/cookies.py))
   - `load_cookie_cache_from_config()` → Parse persisted cookies from TOML with timestamps
   - `save_cookies_to_cache(domain, cookies)` → Persist cookies back to config with current timestamp
   - `prune_expired_cookies()` → Remove stale entries from config file

### 4. Update CLI to accept user and env parameters ([src/browser_launcher/cli.py](src/browser_launcher/cli.py))
   - Add `--user` argument to `launch` command (default: "default")
   - Add `--env` argument to `launch` command (default: "prod")
   - Pass these to the browser launcher for cookie lookup
   - Update CLI help text to document the hierarchical cookie configuration
   - Usage: `poetry run browser-launcher launch https://example.com --user john --env production`

### 5. Create integration hook ([src/browser_launcher/browsers/base.py](src/browser_launcher/browsers/base.py) and [cookies.py](src/browser_launcher/cookies.py))
   - Add `inject_and_verify_cookies(launcher: BrowserLauncher, domain, user, env)` function
   - Integrates into `safe_get_address()` or as separate method called after launch
   - Workflow: call safe_get_address() → check cached cookies → if valid, inject and re-call safe_get_address() → write updated cookies back

### 6. Test suite structure (TDD-first approach in [tests/test_cookies.py](tests/test_cookies.py) and [tests/cookies/](tests/cookies/))
   - **Unit tests** (write these FIRST):
     - `test_cookie_validation_ttl` - Verify TTL checking works
     - `test_read_cookies_from_browser` - Mock driver, assert extraction
     - `test_write_cookies_to_browser` - Mock driver, assert injection
     - `test_hierarchical_config_lookup` - Verify user/env/domain precedence
     - `test_cache_persistence_to_toml` - Parse/serialize timestamps
     - `test_is_cookie_valid_expired` - TTL boundary cases
   - **Integration tests**:
     - `test_launch_with_cached_cookies` - Mock browser launch with cookie injection
     - `test_save_cookies_after_navigation` - Verify cookies persisted post-navigation
   - **Config parsing tests**:
     - `test_load_hierarchical_cookie_config` - Valid/invalid TOML structures
     - `test_cookie_name_variants_by_browser` - Browser-specific name resolution
   - **CLI tests**:
     - `test_launch_command_with_user_env_args` - Verify CLI accepts and passes user/env
     - `test_launch_command_default_user_env` - Verify defaults work ("default", "prod")

### 7. Configuration example format (update [src/browser_launcher/assets/default_config.toml](src/browser_launcher/assets/default_config.toml))
   ```toml
   [users.default.prod.api_example_com]
   cookies = [
       {name = "session_id", value = "cached_value", timestamp = "2024-02-11T10:00:00Z"},
       {name = "auth_token", variants = {chrome = "token_chrome", firefox = "token_firefox"}}
   ]
   ttl_seconds = 14400  # Override default 8 hours for this domain
   
   [users.john.production.api_example_com]
   cookies = [
       {name = "session_id", value = "abc123xyz", timestamp = "2024-02-11T10:00:00Z"}
   ]
```
