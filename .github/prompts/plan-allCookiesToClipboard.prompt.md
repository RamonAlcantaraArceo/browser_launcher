## Plan: Modular Launch Actions

Refactor the launch wait loop so key-driven actions are registered through a small internal action registry, structured to support future entry-point discovery, then add a built-in action that exports all browser cookies as a Playwright-style JavaScript snippet and copies it to the system clipboard on macOS. Cover the change with focused unit tests for both snippet generation/clipboard behavior and launch-loop dispatch.

**Steps**
1. Define the wait-loop action abstraction in src/browser_launcher/cli.py or a small adjacent module under src/browser_launcher/.
   Depends on no other step.
   Create a typed action record for: key, help text, handler callable, and optional ordering metadata.
   Add a registry builder for built-in actions so the launch command stops hard-coding help lines and key branches.
   Shape the API so future external discovery can plug in cleanly without changing launch() again.
2. Refactor the current built-in launch actions into registered handlers.
   Depends on 1.
   Convert screenshot capture, session cookie cache, all-cookie cache, and cookie dump into handlers that receive one shared context object rather than many positional arguments.
   Keep quit and Enter handling as core loop behavior unless the implementation naturally supports special keys in the registry without making the code harder to read.
   Generate the help text from the registered actions so the wait-loop instructions stay in sync with the available handlers.
3. Add the cookie-export formatter and clipboard helper.
   Depends on 1.
   Add a function that reads all browser cookies from the current session and renders them as a JavaScript snippet in the exact structure the user requested: async (page) => { await page.context().addCookies([...]); await page.reload(); }.
   Preserve relevant Selenium cookie fields that Playwright accepts or benefits from: name, value, domain, path, secure, httpOnly, sameSite, expiry when present.
   Normalize field names and ordering so output is deterministic for tests.
   Decide how to handle unsupported or absent fields explicitly: omit missing optional properties rather than inserting null placeholders.
   Add a clipboard helper for macOS using pbcopy via subprocess so the feature works without adding a new dependency.
   Make the helper surface user-friendly success/failure messages and log the underlying exception details.
4. Register the new export action in the built-in registry.
   Depends on 2 and 3.
   Bind it to a new single-character hotkey that does not conflict with existing actions.
   Add matching dynamic help text in launch().
   On success, report how many cookies were exported and that the JavaScript was copied to the clipboard.
   On failure, keep the browser session alive and report the error without crashing the wait loop.
5. Add formatter and clipboard tests.
   Parallel with 6 after 3 is implemented.
   In tests/unit/, add focused unit tests for the new formatter to verify:
   deterministic snippet structure;
   correct serialization of booleans, strings, and expiry;
   omission of absent optional fields;
   correct escaping/quoting for cookie values and domains.
   Add tests for the clipboard helper by mocking subprocess invocation instead of touching the real clipboard.
6. Add launch-loop registry and dispatch tests.
   Parallel with 5 after 2 is implemented.
   Extend tests/unit/test_cli_launch.py to verify the launch help text includes the new registered action.
   Add an interactive-loop test that feeds the new hotkey through mocked stdin, asserts the export handler runs, and confirms the browser closes normally afterward.
   Add at least one test that a handler exception is reported to the console/log and does not corrupt terminal teardown.
7. Prepare for future external plugins without committing to entry-point loading yet.
   Depends on 1.
   Document the extension seam in code comments/docstrings and keep a single registry-loading function where entry-point discovery can later be added.
   If the code remains simple, avoid introducing Poetry plugin configuration in this change; the internal registry-plus-context object is enough for the first pass.
8. Verify locally.
   Depends on 5 and 6.
   Run the targeted unit tests first for the touched files.
   Then run at least Ruff check and the relevant pytest subset; optionally run mypy if the new action/context types are non-trivial.

**Relevant files**
- /Users/ramonalcantaraarceo/github/browser_launcher/src/browser_launcher/cli.py — current launch wait loop, existing action branches, and best location for the first internal registry/context object.
- /Users/ramonalcantaraarceo/github/browser_launcher/src/browser_launcher/cookies.py — current browser cookie reading/dumping helpers that can be reused by the export formatter instead of reimplementing cookie access.
- /Users/ramonalcantaraarceo/github/browser_launcher/src/browser_launcher/auth/factory.py — reference pattern for future-ready discovery/caching shape if the action registry later expands to entry points.
- /Users/ramonalcantaraarceo/github/browser_launcher/tests/unit/test_cli_launch.py — existing stdin-driven launch-loop tests to extend for the new registered action and dynamic help text.
- /Users/ramonalcantaraarceo/github/browser_launcher/tests/unit/test_cli_cookie_dump.py — closest existing cookie presentation tests; likely place to add snippet-formatting coverage or to mirror style in a new export-focused test file.
- /Users/ramonalcantaraarceo/github/browser_launcher/pyproject.toml — only needed if the implementation decides to reserve or document a future entry-point group; otherwise likely unchanged in this pass.

**Verification**
1. Run targeted tests covering the new formatter/clipboard helper and the launch hotkey flow.
2. Run poetry run pytest tests/unit/test_cli_launch.py -v and the cookie-formatting test module.
3. Run poetry run ruff check src/ tests/.
4. If new typed structures are introduced, run poetry run mypy src/ tests/.
5. Manual smoke check on macOS: launch the CLI, press the new hotkey, paste the clipboard contents into a scratch file, and confirm the snippet matches the Playwright shape and includes the active browser cookies.

**Decisions**
- Export destination is the system clipboard, not stdout or a file.
- The first pass should use an internal registry plus a future-ready interface, not full external plugin entry-point loading.
- Scope includes modularizing wait-loop actions enough to register new built-ins cleanly.
- Scope excludes designing a general third-party plugin packaging story in this change.
- Recommended implementation uses macOS pbcopy directly to avoid a new runtime dependency.

**Further Considerations**
1. Recommended hotkey: use e for export if available; it is mnemonic and avoids conflicts with current keys.
2. Keep snippet generation in a dedicated helper instead of embedding string building inside the action handler so the formatter is easy to test in isolation.
3. If Playwright compatibility is a priority, validate whether leading-dot cookie domains should be preserved exactly rather than normalized during export; the formatter should mirror browser cookie data unless there is a proven compatibility issue.
