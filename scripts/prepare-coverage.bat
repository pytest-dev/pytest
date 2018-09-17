REM scripts called by AppVeyor to setup the environment variables to enable coverage
if not defined PYTEST_NO_COVERAGE (
    set "COVERAGE_FILE=%CD%\.coverage"
    set "COVERAGE_PROCESS_START=%CD%\.coveragerc"
    set "_PYTEST_TOX_COVERAGE_RUN=coverage run -m"
    set "_PYTEST_TOX_EXTRA_DEP=coverage-enable-subprocess"
    echo Coverage setup completed
) else (
    echo Skipping coverage setup, PYTEST_NO_COVERAGE is set
)
