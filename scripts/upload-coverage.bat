REM script called by Azure to combine and upload coverage information to codecov
if "%PYTEST_COVERAGE%" == "1" (
    echo Prepare to upload coverage information
    if defined CODECOV_TOKEN (
        echo CODECOV_TOKEN defined
    ) else (
        echo CODECOV_TOKEN NOT defined
    )
    %PYTHON% -m pip install codecov
    %PYTHON% -m coverage combine
    %PYTHON% -m coverage xml
    %PYTHON% -m coverage report -m
    scripts\retry %PYTHON% -m codecov --required -X gcov pycov search -f coverage.xml --name %PYTEST_CODECOV_NAME%
) else (
    echo Skipping coverage upload, PYTEST_COVERAGE=%PYTEST_COVERAGE%
)
