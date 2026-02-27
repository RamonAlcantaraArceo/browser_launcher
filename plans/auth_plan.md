User: Help me generate a step by step plan in the mode of prompts that can be used later to perform: Custom authentication flow
    # the idea is the project can be extended by other users and they can
    # implement their own authentication mechanism. If desired cookie is not 
    # present in the cache, we can call an external module to perform
    # authentication and get the cookies, then inject those cookies into the browser.
    # and save them to cache for future use. this way next time when user launches
    # the browser, cookies will be present in the cache and can be injected directly.

## Plan: Custom Authentication Flow Framework

**TL;DR**: Build a modular authentication system that delegates to external auth modules via Python entry points, integrates with existing cookie management, and provides interactive retry on failures. The framework handles module discovery, configuration, and cookie caching while auth modules focus solely on returning cookie data.

**Steps**

1. **Create authentication abstractions** in src/browser_launcher/auth/
   - `AuthResult` dataclass for returned cookie data and metadata
   - `AuthenticatorBase` abstract class with `authenticate()` method
   - `AuthError` exception hierarchy for different failure types
   - `AuthConfig` dataclass for module configuration

2. **Implement module discovery system** in src/browser_launcher/auth/factory.py
   - `AuthFactory.discover_modules()` using entry points (`browser_launcher.authenticators`)
   - `AuthFactory.create()` for instantiating auth modules with config
   - Module caching and validation
   - Configuration schema validation per module

3. **Add authentication configuration** to config.py
   - Extend TOML schema: `[auth]`, `[auth.{module_name}]`, `[users.{user}.{env}.auth]`
   - `get_auth_config()` method with hierarchical user/env resolution
   - Authentication timeout and retry settings
   - Module-specific configuration loading

4. **Integrate authentication hook** in cli.py
   - Replace TODO comment with `attempt_authentication()` call
   - Check for cached valid cookies first (existing `inject_and_verify_cookies`)
   - If no cached cookies, load and execute auth module
   - Interactive retry mechanism with credential prompts
   - Save returned cookies using existing `CookieConfig.update_cookie_cache`

5. **Build interactive retry system** in src/browser_launcher/auth/retry.py 
   - `AuthRetryHandler` class for managing retry attempts
   - Input prompts for different/same credentials or continue without auth
   - Timeout handling and max retry limits from config
   - User-friendly error messages via Rich console

6. **Add comprehensive authentication logging** throughout auth module
   - Module discovery and loading events (INFO level)
   - Authentication attempts and results (INFO/WARNING level)
   - Configuration validation issues (WARNING level)
   - Detailed error tracing for module failures (DEBUG level)

7. **Create example authentication module** in examples/auth_modules/form_auth.py
   - Implement `AuthenticatorBase` for basic form authentication
   - Configure via entry points in pyproject.toml
   - Document configuration requirements and cookie return format
   - Include error handling and timeout management

8. **Write comprehensive tests** following TDD approach
   - `tests/unit/test_auth_factory.py` for module discovery and creation
   - `tests/unit/test_auth_config.py` for configuration loading
   - `tests/unit/test_auth_retry.py` for retry mechanism
   - `tests/unit/test_cli_auth.py` for CLI integration
   - `tests/smoke/test_auth_integration.py` for end-to-end flows
   - Mock external auth services and entry points

   **Status (implemented):** CLI authentication integration tests were split out into `tests/unit/test_cli_auth.py`, with `tests/unit/test_cli_launch.py` kept focused on launch behavior. Current run: `27 passed` for `test_cli_auth.py` + `test_cli_launch.py`.

9. **Update configuration templates** in default_config.toml
   - Add `[auth]` section with default settings
   - Document configuration structure and examples
   - Include timeout, retry, and module settings

**Verification**
- Run `poetry run pytest tests/unit/test_auth_*.py -v` for unit tests
- Run `poetry run browser-launcher launch --user test --env dev example.com` with auth configured
- Verify auth module discovery: `poetry run python -c "from browser_launcher.auth.factory import AuthFactory; print(AuthFactory.discover_modules())"`
- Test retry mechanism by providing invalid credentials intentionally
- Verify cookie caching after successful authentication

**Decisions**
- **Entry points over config paths**: More standard Python packaging approach
- **Delegation pattern**: Auth modules only return cookies, framework handles integration  
- **Interactive retry**: Better UX than silent failures or hard exits
- **Hierarchical config**: Consistent with existing user/env/domain structure
- **Graceful degradation**: Failed auth doesn't prevent browser launch
