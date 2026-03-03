## Prompt: Integrating Allure Reporting and Enhancing Pytest Execution

We want to significantly improve our test reporting and execution workflow for the browser_launcher project. Please address the following goals:

### 1. Allure Integration for Pytest

- Integrate Allure as a reporting tool for pytest.
- Ensure that Selenium/browser logs, screenshots, and artifacts are attached to Allure reports for each test (especially on failure).
- Make sure Allure reports are generated and persisted in CI, and can be browsed locally by developers.
- Document how to view Allure reports locally and in CI artifacts.

### 2. Selenium Log Retention

- Ensure that per-browser Selenium logs (console, network, driver logs, screenshots) are captured and attached to the corresponding Allure test case, so that no details are lost even if the test fails or is run in parallel.
- Propose a pattern for capturing and attaching logs/screenshots in pytest fixtures or hooks.

### 3. Pytest Plugin Enhancements

- Add or configure pytest plugins to:
  - Execute tests in random order (e.g., pytest-randomly) to surface hidden dependencies.
  - Run tests in parallel (e.g., pytest-xdist) for faster feedback.
  - Ensure that Allure reporting and log capture work correctly with parallel and randomized execution.
- Document any changes to pytest invocation (e.g., new flags, environment variables).

### 4. CI/CD and Developer Workflow

- Update CI configuration to:
  - Install Allure and required pytest plugins.
  - Generate and upload Allure reports as build artifacts.
  - Optionally, publish Allure reports to a static site or dashboard.
- Provide local developer instructions for running tests with Allure and viewing reports.

---

**Please propose a step-by-step plan for integrating Allure, capturing Selenium logs, and enhancing pytest execution with random and parallel plugins. Include any changes to requirements, pytest.ini, CI scripts, and developer documentation.**
