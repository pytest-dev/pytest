"""Test for https://github.com/pytest-dev/pytest/issues/519."""


def test_510(testdir):
    testdir.copy_example("issue_519.py")
    result = testdir.runpytest("issue_519.py")
    result.stdout.fnmatch_lines(
        [
            "collected 0 items / 1 error",
            "",
            "*= ERRORS =*",
            "*_ ERROR collecting issue_519.py _*",
            'In function "test_one":',
            'Parameter "arg1" should be declared explicitly via indirect or in function itself',
            "*= short test summary info =*",
            "ERROR issue_519.py",
            "*! Interrupted: 1 error during collection !*",
            "*= 1 error in *=",
        ]
    )
