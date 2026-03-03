Objective
- Change Allure hierarchy from:
  tests.unit -> test_module -> Python X.Y -> test_case
  to:
  tests.unit -> Python X.Y -> test_module -> test_case
- Keep CI metadata validation working.

Scope
- In scope:
  - tests/conftest.py (Allure labeling logic)
  - tests/unit/test_conftest_allure_matrix_metadata.py (unit expectations)
- Optional hardening:
  - .github/workflows/test-allure.yml validator script cleanup
- Out of scope:
  - Non-Allure test behavior
  - Browser launcher runtime logic unrelated to reporting

Implementation Checklist
1) Preserve CI-compatible Python metadata
- Keep dynamic parameter:
  - allure.dynamic.parameter("python_version", "Python X.Y")
- Reason:
  - CI validator already reads this parameter and should stay green.
- Acceptance criteria:
  - Each `*-result.json` includes parameter `python_version` with value `Python X.Y`.

2) Re-map Allure hierarchy labels in conftest
- In autouse fixture (or setup hook), set:
  - parent suite = `tests.unit`
  - suite = `Python X.Y`
  - sub suite = module name (e.g., `test_auth_config`)
- Derive module name from request node/module path (stable and deterministic).
- Acceptance criteria:
  - Allure tree groups by Python version directly under `tests.unit`.
  - Within each Python version, tests are grouped by module.

3) Update unit tests for conftest behavior
- Adjust expectations in:
  - tests/unit/test_conftest_allure_matrix_metadata.py
- Validate that:
  - parameter is still emitted
  - suite/subSuite mappings changed as intended
- Acceptance criteria:
  - Updated test file passes locally.

4) Validate locally (targeted)
- Run:
  - poetry run pytest tests/unit/test_conftest_allure_matrix_metadata.py -v
- Acceptance criteria:
  - All targeted tests pass.

5) Validate report shape (practical check)
- Run a small unit subset with Allure output:
  - poetry run pytest tests/unit/ --alluredir=allure-results -q
- Generate/open report as needed.
- Acceptance criteria:
  - Hierarchy appears as:
    - tests.unit
      - Python 3.13 (or local version/env)
        - test_auth_config
        - test_auth_dummy

6) Optional CI validator hardening (recommended)
- In workflow validator script:
  - Unnest label scanning from parameter loop
  - Fail on missing expected labels (`sys.exit(1)`)
- Keep backwards compatibility by still reading both parameter and label paths.
- Acceptance criteria:
  - Workflow step fails when a matrix version is absent from merged results.

Risk Notes
- If only subSuite is changed and parameter removed, CI may miss versions depending on script path.
- Allure adapters can differ slightly; explicit parent/suite/subSuite is the safest way to force hierarchy.

Definition of Done
- Conftest emits:
  - `python_version` parameter
  - parent/suite/subSuite mapped to desired hierarchy
- Updated unit tests pass.
- Generated Allure report shows desired grouping.
- (Optional) CI validator is stricter and deterministic.
