
## Plan: Matrix-aware Allure grouping (FULLY IMPLEMENTED)

This plan has been **fully implemented**. The project now keeps a single GitHub Pages Allure report, with each Python-version execution as a distinct test instance so the total reflects all matrix runs (target: ~5× current count). Per-test version identity is added in pytest metadata (not categories), and the merge/generate flow includes strong validation. Categories remain reserved for failure taxonomy and are not used for version separation.


**Implementation Summary**
- [x] Tests for Allure metadata behavior are present in [tests/conftest.py](tests/conftest.py).
- [x] An `autouse` fixture in [tests/conftest.py](tests/conftest.py) reads the matrix version from the environment and applies `allure.dynamic.parameter` (identity key) and `allure.dynamic.sub_suite` (UI grouping label: “Python 3.x”).
- [x] [.github/workflows/test-allure.yml](.github/workflows/test-allure.yml) passes the matrix version into pytest runtime (env var) for each shard and uses artifact naming per version.
- [x] The workflow merges artifacts into one folder and includes explicit pre-generate and post-generate assertions (raw file count > 0, generated `summary.json` total > 0, and matrix-aware sanity check).
- [x] The publish job adds run-level metadata (single `executor.json` with run URL + workflow context, and a merged `environment.properties` summarizing matrix versions) so report widgets show provenance consistently.
- [x] Allure docs ([README.md](README.md), [ALLURE_SETUP_VERIFIED.md](ALLURE_SETUP_VERIFIED.md)) are updated to reflect semantics, expectations, and troubleshooting for matrix runs.


**Verification**
- CI job-level: Each matrix shard uploads a non-empty `allure-results-*` artifact.
- Merge job: Merged raw files count approximates the sum of all shards.
- Generated report: [allure-report/widgets/summary.json](allure-report/widgets/summary.json) shows increased total (expected around 1345 for 5×269).
- UI checks on gh-pages: `Suites` shows Python-version grouping; individual tests show the `python_version` parameter.
- Regression check: Existing local test commands still pass (`poetry run pytest tests/ -v`).


**Decisions**
- Chosen: per-test `python_version` parameter + sub-suite label (solves identity collision and improves navigation).
- Not chosen: categories for version split (wrong purpose; keep for failure classification later).
- Scope: Unit matrix is implemented; smoke integration can be added with the same metadata pattern if needed.
