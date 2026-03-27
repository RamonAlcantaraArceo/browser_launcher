## Plan: Clipboard Cookie Export Only

Implement only the current-state feature: add one new launch-loop hotkey that exports all browser cookies as a Playwright-style JavaScript snippet and copies it to the macOS clipboard. Do this in the existing `if/elif` loop (no action registry/plugin refactor in this pass), with focused tests for formatter, clipboard copy, and hotkey dispatch.

**Steps**
1. Add a formatter helper for Playwright cookie script output in `src/browser_launcher/cli.py` (or `src/browser_launcher/cookies.py` if it better matches existing cookie helpers).
   Build exact structure:
   `async (page) => { await page.context().addCookies([...]); await page.reload(); }`.
   Serialize cookies as JS object literals with stable key ordering for deterministic tests.
   Include fields when present: `name`, `value`, `domain`, `path`, `httpOnly`, `secure`, `sameSite`, `expiry`.
   Omit optional fields that are missing.
2. Add a clipboard helper for macOS using `pbcopy`.
   Use `subprocess.run([...], input=..., text=True, check=True)` to copy the generated script.
   Return/raise in a way that allows clean console + logger messaging.
   Keep failure non-fatal to the launch session.
3. Add an export command function that reads current browser cookies and copies the JS to clipboard.
   Reuse existing cookie read pattern (`driver.get_cookies()` or existing helper behavior used by cache/dump flow).
   If no cookies exist, print warning and skip clipboard call.
   On success, print a short confirmation with cookie count.
4. Wire the new hotkey into the existing launch wait loop in `src/browser_launcher/cli.py`.
   Add one help line near:
   `Press 'c' to dump all cookies from the browser.`
   Add one `elif` branch (recommended key `e`) to invoke the export-to-clipboard function.
   Keep existing keys (`Enter`, `s`, `a`, `c`, `q`) unchanged.
5. Add unit tests for formatter and clipboard helper.
   Validate exact script envelope and cookie object rendering.
   Validate quoting/escaping behavior for string values.
   Validate optional-field omission.
   Mock `subprocess.run` to assert `pbcopy` invocation without touching real clipboard.
6. Extend launch-loop tests for the new key path.
   In `tests/unit/test_cli_launch.py`, add/extend tests using mocked `sys.stdin.read` to send `e` then exit.
   Assert help text includes the new key description.
   Assert export function is called and CLI exits cleanly with browser close.
   Add one error-path test: export helper raises, error is reported, loop continues/tears down safely.
7. Run targeted verification.
   Run affected unit tests first.
   Then run `poetry run ruff check src/ tests/`.
   Optional: run `poetry run mypy src/ tests/` if new types/signatures were introduced.

**Relevant files**
- `/Users/ramonalcantaraarceo/github/browser_launcher/src/browser_launcher/cli.py` — add helper(s), hotkey help text, and wait-loop `elif` branch.
- `/Users/ramonalcantaraarceo/github/browser_launcher/src/browser_launcher/cookies.py` — optional placement/reuse for cookie formatting/read helpers.
- `/Users/ramonalcantaraarceo/github/browser_launcher/tests/unit/test_cli_launch.py` — add hotkey + dispatch + error-path tests.
- `/Users/ramonalcantaraarceo/github/browser_launcher/tests/unit/test_cli_cookie_dump.py` — extend for formatter tests, or create a new nearby export-focused unit file.

**Verification**
1. Run formatter/clipboard unit tests.
2. Run `poetry run pytest tests/unit/test_cli_launch.py -v`.
3. Run cookie export formatter tests.
4. Run `poetry run ruff check src/ tests/`.
5. Manual macOS check: launch CLI, press `e`, paste clipboard to confirm exact snippet format.

**Decisions**
- Included scope: direct implementation in the current launch loop.
- Excluded scope: plugin model / registry refactor / entry-point discovery.
- Output target: system clipboard only.
- Platform target for this pass: macOS via `pbcopy`.
