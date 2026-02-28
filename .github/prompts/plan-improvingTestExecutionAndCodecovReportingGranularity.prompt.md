## Prompt: Improving Test Execution and Codecov Reporting Granularity

We currently use pytest and Codecov for test execution and coverage reporting. However, our workflow could benefit from more granular and actionable coverage insights. Please review and propose improvements for the following areas:

1. **Test Execution Strategy**
   - How can we better organize or parametrize our tests to ensure all code paths (including edge cases and error handling) are exercised?
   - Should we split unit, integration, and smoke tests into separate jobs or stages for clearer reporting and faster feedback?
   - Are there pytest plugins or flags (e.g., `--cov-branch`, `--cov-report=xml`, `--cov-fail-under`) we should adopt for stricter or more informative runs?

2. **Coverage Collection**
   - Are we using the optimal pytest-cov configuration to capture branch and partial coverage, not just line coverage?
   - Should we generate multiple coverage reports (e.g., per test type, per module) for more targeted analysis?
   - How can we ensure that coverage is collected for subprocesses, CLI entry points, and dynamic imports?

3. **Codecov Integration**
   - How can we configure Codecov to provide more granular insights (e.g., per-folder, per-component, or per-test-type coverage)?
   - Should we use Codecov YAML to define custom coverage groups, status checks, or thresholds for critical files?
   - Are there Codecov flags or environment variables we should set in CI to distinguish between test types or platforms?

4. **Reporting and Feedback**
   - How can we make coverage feedback more actionable for developers (e.g., PR comments, status checks, coverage diffs)?
   - Should we fail CI on coverage drops, or only for critical files?
   - Are there tools or scripts we should add to automate local coverage checks before pushing?

**Please propose a revised test and coverage workflow, including any changes to pytest invocation, CI configuration, and Codecov YAML.**
