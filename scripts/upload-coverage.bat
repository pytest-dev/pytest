REM script called by AppVeyor to combine and upload coverage information to codecov
if not defined PYTEST_NO_COVERAGE (
    echo Prepare to upload coverage information
    if defined CODECOV_TOKEN (
        echo CODECOV_TOKEN defined
    ) else (
        echo CODECOV_TOKEN NOT defined
    )
    python -m pip install codecov
    coverage combine
    coverage xml --ignore-errors
    coverage report -m --ignore-errors
    scripts\retry codecov --required -X gcov pycov search -f coverage.xml --flags windows
) else (
    echo Skipping coverage upload, PYTEST_NO_COVERAGE is set
)
