REM script called by AppVeyor to combine and upload coverage information to codecov
if not defined PYTEST_NO_COVERAGE (
    echo Prepare to upload coverage information
    C:\Python36\Scripts\pip install codecov
    C:\Python36\Scripts\coverage combine
    C:\Python36\Scripts\coverage xml --ignore-errors
    C:\Python36\Scripts\coverage report -m --ignore-errors
    C:\Python36\Scripts\codecov --required -X gcov pycov search -f coverage.xml --flags %TOXENV:-= % windows
) else (
    echo Skipping coverage upload, PYTEST_NO_COVERAGE is set
)
