## Plan: Matrix-aware Allure grouping (DRAFT)

This plan keeps a single GitHub Pages Allure report, but makes each Python-version execution a distinct test instance so the total reflects all matrix runs (target: ~5× current count). The core change is to add stable per-test version identity in pytest metadata (not categories), then keep merge/generate flow as-is with stronger validation. Categories are for failure taxonomy and are not the right primitive for version separation.

When implementing ask for confirmation before moving to next step.

**Steps**
1. Add tests first for new Allure metadata behavior in [tests](tests), targeting [tests/conftest.py](tests/conftest.py) hooks/fixtures.
2. In [tests/conftest.py](tests/conftest.py), add an `autouse` fixture that reads matrix version from env and applies `allure.dynamic.parameter` (identity key) plus `allure.dynamic.sub_suite` (UI grouping label: “Python 3.x”).
3. In [.github/workflows/test-allure.yml](.github/workflows/test-allure.yml), pass matrix version into pytest runtime (env var) for each shard and keep artifact naming per version.
4. In [.github/workflows/test-allure.yml](.github/workflows/test-allure.yml), retain artifact merge into one folder, but add explicit pre-generate and post-generate assertions (raw file count > 0, generated `summary.json` total > 0, and matrix-aware sanity check).
5. Add run-level metadata in the publish job (single `executor.json` with run URL + workflow context, and a merged `environment.properties` summarizing matrix versions) so report widgets show provenance consistently.
6. Update Allure docs to reflect semantics and expectations in [README.md](README.md) and [ALLURE_SETUP_VERIFIED.md](ALLURE_SETUP_VERIFIED.md): suites/categories meaning, why totals increase with matrix, and how to troubleshoot empties.

**Verification**
- CI job-level: confirm each matrix shard uploads non-empty `allure-results-*` artifact.
- Merge job: confirm merged raw files count approximates shard sum.
- Generated report: validate [allure-report/widgets/summary.json](allure-report/widgets/summary.json) shows increased total (expected around 1345 for 5×269).
- UI checks on gh-pages: `Suites` shows Python-version grouping; individual tests show `python_version` parameter.
- Regression check: existing local test commands still pass (`poetry run pytest tests/ -v`).

**Decisions**
- Chosen: per-test `python_version` parameter + sub-suite label (solves identity collision and improves navigation).
- Not chosen: categories for version split (wrong purpose; keep for failure classification later).
- Scope now: unit matrix only; smoke integration deferred and can be added with same metadata pattern later.
